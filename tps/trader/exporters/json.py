import logging

import json
import os
import shutil

import subprocess

from .base import BaseExporter



logger = logging.getLogger(__name__)

__all__ = ["JSONExporter"]


class JSONExporter(BaseExporter):

    short_name = "json_file"

    TESTS_DIR_NAME = "tests"
    SOLUTION_DIR_NAME = "solutions"
    VALIDATOR_DIR_NAME = "validators"
    SUBTASKS_DIR_NAME = "subtasks"
    CHECKER_DIR_NAME = "checker"
    GRADER_DIR_NAME = "graders"
    OTHER_FILES_DIR_NAME = "others"

    def __init__(self, revision):
        super().__init__(revision)

    def _do_export(self):

        def export_resources_to_path(prefix):
            for resource in self.revision.resource_set.all():
                self.extract_from_storage_to_path(
                    resource.file,
                    os.path.join(
                        prefix,
                        resource.name
                    )
                )

        def generate_clean_name(name):
            return name.replace(' ', '_').lower()

        # Exporting problem global data

        problem_data = self.revision.problem_data

        problem_data_dict = {
            "code": problem_data.code_name,
            "name": problem_data.title,
            "time_limit": problem_data.time_limit,
            "memory_limit": problem_data.memory_limit,
            "score_precision": problem_data.score_precision,
        }
        if problem_data.task_type:
            problem_data_dict.update({
                "task_type": problem_data.task_type,
                "task_type_params": problem_data.task_type_parameters,
            })

        self.write_to_file(
            "problem.json".format(problem_code=problem_data.code_name),
            json.dumps(problem_data_dict)
        )

        self.write_to_file(
            "statement.md",
            self.revision.statement_set.get().content
        )

        # Exporting problem files
        self.create_directory(self.OTHER_FILES_DIR_NAME)
        for file in self.revision.problem.files.all():
            self.extract_from_storage_to_path(
                file,
                os.path.join(
                    self.OTHER_FILES_DIR_NAME,
                    file.name
                )
            )


        # Exporting testcases

        self.create_directory(self.TESTS_DIR_NAME)
        ignored_testcases = []

        for testcase in self.revision.testcase_set.all():
            if not testcase.input_file_generated() or not testcase.output_file_generated():
                ignored_testcases.append(testcase)
                logger.warning("Testcase {} couldn't be generated. Skipping".format(testcase.name))
                continue

            self.extract_from_storage_to_path(
                testcase.input_file,
                os.path.join(
                    self.TESTS_DIR_NAME,
                    "{testcase_name}.in".format(testcase_name=generate_clean_name(testcase.name))
                ),
            )
            self.extract_from_storage_to_path(
                testcase.output_file,
                os.path.join(
                    "tests",
                    "{testcase_name}.out".format(testcase_name=generate_clean_name(testcase.name))
                )

            )

        # Exporting graders
        self.create_directory(self.GRADER_DIR_NAME)
        for grader in self.revision.grader_set.all():
            self.extract_from_storage_to_path(
                grader.code,
                os.path.join(
                    self.GRADER_DIR_NAME,
                    grader.name,
                )
            )

        # Exporting subtasks

        self.create_directory(self.SUBTASKS_DIR_NAME)
        for subtask in self.revision.subtasks.all():
            self.write_to_file(
                os.path.join(
                    self.SUBTASKS_DIR_NAME,
                    "{subtask_index:02}-{subtask_name}.json".format(
                    subtask_index=subtask.index,
                    subtask_name=subtask.name,
                )),
                json.dumps(
                    {
                        "score": subtask.score,
                        "testcases":
                            [
                                generate_clean_name(t.name)
                                for t in subtask.testcases.all()
                            ]
                    }
                )
            )

        # Exporting solutions

        self.create_directory(self.SOLUTION_DIR_NAME)
        for solution in self.revision.solution_set.all():
            if solution.verdict:
                solution_dir = os.path.join(self.SOLUTION_DIR_NAME, generate_clean_name(solution.verdict.name))
            else:
                solution_dir = os.path.join(self.SOLUTION_DIR_NAME, "unknown_verdict")
            self.create_directory(solution_dir)
            self.extract_from_storage_to_path(solution.code, os.path.join(solution_dir, solution.name))

        # We don't export generators. Tests are already generated so there is no use for them

        # Exporting checker( We only extract main checker)
        self.create_directory(self.CHECKER_DIR_NAME)
        for resource in self.revision.checker_set.all():
            self.extract_from_storage_to_path(
                resource.file,
                os.path.join(self.CHECKER_DIR_NAME, resource.name)
            )
        checker = problem_data.checker
        if checker is not None:
            self.extract_from_storage_to_path(
                checker.file,
                os.path.join(self.CHECKER_DIR_NAME, "checker{ext}".format(
                    ext=os.path.splitext(checker.name)[1]
                ))
            )
        export_resources_to_path("checker")

        # Exporting validators
        self.create_directory(self.VALIDATOR_DIR_NAME)
        for validator in self.revision.validator_set.all():
            dirs = []
            for subtask in validator.subtasks:
                dirs.append(subtask.name)
            for dir in dirs:
                full_dir = os.path.join(self.VALIDATOR_DIR_NAME, dir)
                self.create_directory(full_dir)
                self.extract_from_storage_to_path(
                    validator.file,
                    os.path.join(
                        full_dir,
                        validator.name
                    )
                )
        export_resources_to_path("validators")

        # Exporting public
        self.create_directory("repo")

        os.system('git --git-dir="{repo_dir}" worktree add {work_dir} {commit_id}'.format(
            repo_dir=self.revision.repository_path,
            work_dir=self.get_absolute_path("repo"),
            commit_id=self.revision.commit_id
        ))

        tests_dir_in_repo = os.path.join('repo', 'tests')
        self.create_directory(tests_dir_in_repo)

        for testcase in self.revision.testcase_set.all():
            if not testcase.input_file_generated() or not testcase.output_file_generated():
                ignored_testcases.append(testcase)
                logger.warning("Testcase {} couldn't be generated. Skipping".format(testcase.name))
                continue

            self.extract_from_storage_to_path(
                testcase.input_file,
                os.path.join(
                    tests_dir_in_repo,
                    "{testcase_name}.in".format(testcase_name=testcase.name)
                ),
            )
            self.extract_from_storage_to_path(
                testcase.output_file,
                os.path.join(
                    tests_dir_in_repo,
                    "{testcase_name}.out".format(testcase_name=testcase.name)
                )

            )
        
        try:
            print(subprocess.check_output(['tps', 'make-public'], cwd=self.get_absolute_path("repo"), stderr=subprocess.STDOUT))
        except subprocess.CalledProcessError as e:
            print(e.output)
            raise e

        self.create_directory("attachments")
        try:
            shutil.move(os.path.join(self.get_absolute_path("repo"),
                                     "{}.zip".format(problem_data.code_name)),
                        self.get_absolute_path("attachments"))
        except OSError:
            try:
                shutil.move(os.path.join(self.get_absolute_path("repo"),
                                         "{}.zip".format(problem_data.code_name)),
                            self.get_absolute_path("attachments"))
            except OSError as e:
                logger.error("Public archive not found")
                raise e

        shutil.rmtree(self.get_absolute_path("repo"))
