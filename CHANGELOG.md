# CHANGELOG

## v0.4.0 (2024-07-17)

### Chore

* chore: Remove unnecessary logging statement

Removed a redundant logging statement within the `Note` class, simplifying the code and enhancing performance by eliminating unnecessary overhead. ([`b20fb9e`](https://github.com/RedAtman/simplenote/commit/b20fb9e8e9f5384ee5d79987b086e9e8e0913b15))

* chore: Remove example settings file

The example settings file is no longer needed, as the plugin now automatically creates a default settings file when first installed. This simplifies the setup process and ensures users always have a usable configuration. ([`4e407ee`](https://github.com/RedAtman/simplenote/commit/4e407ee65a37cad4d4c033f2f010495b716d74e2))

### Feature

* feat: Add autosave debounce setting

Adds a configurable autosave debounce setting to avoid sending unnecessary save requests when the user is typing. The debounce time is now configurable in the &#34;simplenote.sublime-settings&#34; file. ([`215ea73`](https://github.com/RedAtman/simplenote/commit/215ea73db61d70253f207a439a90f2254c811bca))

* feat: Add initial configuration settings

Adds initial configuration settings for the SimpleNote plugin. These settings allow for customization of synchronization behavior, conflict resolution, and file extension support. The plugin now supports automatically synchronizing notes upon startup, syncing at regular intervals, and customizing the number of notes synced per session. Additionally, the plugin allows for managing file extension mapping based on note titles, which enables seamless integration with other plugins like PlainTasks. ([`3c0694e`](https://github.com/RedAtman/simplenote/commit/3c0694e2f3fdb117a02ca2e027b924b81d064fe3))

### Unknown

* Merge pull request #14 from RedAtman/dev

Dev ([`4fb3682`](https://github.com/RedAtman/simplenote/commit/4fb36829735a5e8563c70b25c865f58a47de3b93))

* Merge pull request #13 from RedAtman/dev

Dev ([`9758d69`](https://github.com/RedAtman/simplenote/commit/9758d6909b2d483485c61292cafebc31b81ae078))

* Fix: Remove redundant syntax file setting

Removed redundant code that attempted to set the syntax file for new notes. This setting is already handled elsewhere in the plugin. ([`57a4546`](https://github.com/RedAtman/simplenote/commit/57a454648948409a30108ea65d16fb4dd420929d))

* Refactor: Rename classes and commands for consistency

Renamed classes and commands to use &#34;Simplenote&#34; prefix for better organization and consistency. This change ensures a clear distinction between internal and user-facing elements. ([`9864fc0`](https://github.com/RedAtman/simplenote/commit/9864fc00c10afe72324c845eeda634d55c569f1b))

* Fix: Adjust ignored files

Removed unnecessary ignored files and added new files that should be ignored. This ensures that only relevant files are tracked in the repository. ([`d705e56`](https://github.com/RedAtman/simplenote/commit/d705e56a217cc078d5e03353514ab67ad76c9da6))

* Fix: Removed redundant keybindings

Removed keybindings from `Default.sublime-keymap` for note-related commands as they were redundant and caused conflicts. ([`a3e4c77`](https://github.com/RedAtman/simplenote/commit/a3e4c7785921251956be6be6cc6da7f0eaa7ef11))

## v0.3.0 (2024-07-17)

### Feature

* feat: Automate release creation and tagging

Introduce a new workflow to automatically create releases and tags based on the `RELEASE_VERSION` environment variable. This workflow leverages the `latest-tag` and `bump-everywhere` actions to simplify the release process and ensure consistent versioning across all project components. ([`2277ec0`](https://github.com/RedAtman/simplenote/commit/2277ec05d11e1f2fcba76d7a6320ab508ff26095))

* feat: Add debug information to release workflow

Add debug information to the release workflow to help troubleshoot potential issues. This change prints the current git status, the last commit log, and the remote URLs for the repository. ([`b3bc3f3`](https://github.com/RedAtman/simplenote/commit/b3bc3f39bcf331b0fead1164b70762f0feafe7b2))

* feat: Automate release creation on merge

Adds a GitHub workflow to automatically create releases and tags on successful merges to the `master` branch. This workflow calculates a new version based on the latest existing tag, creates a tag, pushes it to the remote repository, and publishes a GitHub release. ([`a6a4f62`](https://github.com/RedAtman/simplenote/commit/a6a4f62ffedcc9ae75afeab5a5e5a910069885a3))

### Unknown

* Merge pull request #12 from RedAtman/misc_github_workflows

feat: Automate release creation and tagging ([`6483bf6`](https://github.com/RedAtman/simplenote/commit/6483bf692c529a6ea77ce8a5cc9bfc7b8332f37c))

* Merge pull request #11 from RedAtman/misc_github_workflows

Fix: Release workflow fails to retrieve latest tag ([`c1f6aae`](https://github.com/RedAtman/simplenote/commit/c1f6aae248da8160446a72856d7d41d9b48a4fd3))

* Fix: Release workflow fails to retrieve latest tag

The workflow was incorrectly retrieving the latest tag, causing the release process to fail. This commit fixes the issue by using the `GITHUB_REF` environment variable to get the tag name and sets it as an output variable. This ensures that the latest tag is correctly identified and used for calculating the new release version. ([`1f76548`](https://github.com/RedAtman/simplenote/commit/1f76548aa378a097975b59f762c1bb5b96219222))

* Merge pull request #10 from RedAtman/misc_github_workflows

Fix: Release workflow gets latest tag without version number ([`eb3385f`](https://github.com/RedAtman/simplenote/commit/eb3385fbb20e9e8f4b87119fa82fad142f6ec7e2))

* Fix: Release workflow gets latest tag without version number

The `git describe` command was previously returning the latest tag with the version number. This commit updates the command to only return the latest tag name, ensuring accurate release creation. ([`9479836`](https://github.com/RedAtman/simplenote/commit/9479836c56d44df42a5f98708138c5fd7512b26f))

* Merge pull request #9 from RedAtman/misc_github_workflows

Fix: Use latest tag for release ([`fd17ad1`](https://github.com/RedAtman/simplenote/commit/fd17ad130d6121870cd3b2f35e0da75041e0e52b))

* Fix: Use latest tag for release

The previous logic for fetching the latest tag was incorrect. This commit updates the workflow to use the latest tag directly, ensuring accurate release creation. ([`1f421fb`](https://github.com/RedAtman/simplenote/commit/1f421fba4800d2a08af8c1829ef3816773bfa566))

* Merge pull request #8 from RedAtman/dev

Fix: Ensure Simplenote environment variables are set ([`e48c860`](https://github.com/RedAtman/simplenote/commit/e48c8601ccc2e4b5d52a878d074f4652cb2473ac))

* Fix: Ensure Simplenote environment variables are set

Removed redundant check for Simplenote environment variables. The check was unnecessary as all required variables are already defined and validated by the code. This ensures a cleaner and more efficient codebase. ([`61c2dbf`](https://github.com/RedAtman/simplenote/commit/61c2dbf64deb7a87e5c54ef0c48c82d63eb9569b))

* Merge pull request #7 from RedAtman/misc_github_workflows

Upgrade `actions/checkout` action ([`1f283e4`](https://github.com/RedAtman/simplenote/commit/1f283e404ffc97987263a2336932f3e6f9c3a8bf))

* Upgrade `actions/checkout` action

Updated the `actions/checkout` action to version 4 for improved performance and reliability. This aligns with the latest best practices and ensures compatibility with the latest GitHub features. ([`524b69e`](https://github.com/RedAtman/simplenote/commit/524b69e47260c1489db540f9d053b2487d6c329a))

* Merge pull request #6 from RedAtman/misc_github_workflows

feat: Add debug information to release workflow ([`cd03562`](https://github.com/RedAtman/simplenote/commit/cd035629acb39b60ed817c30c882fdb402ec8b24))

* Merge pull request #5 from RedAtman/misc_github_workflows

Fix: Ensure bash shell is used in create-release workflow ([`1e3e581`](https://github.com/RedAtman/simplenote/commit/1e3e581e21cdff2a1489dffe77d6a0ad9cb27370))

* Fix: Ensure bash shell is used in create-release workflow

Explicitly set the shell to bash in the create-release workflow to prevent issues with environment variables and command execution. This ensures consistent behavior across different GitHub Actions environments. ([`9551b7f`](https://github.com/RedAtman/simplenote/commit/9551b7f13b0a522d108c9f6e90d62061a926e5ca))

* Merge pull request #4 from RedAtman/misc_github_workflows

feat: Automate release creation on merge ([`25fc238`](https://github.com/RedAtman/simplenote/commit/25fc2380137548ec8fce211d9fcbd8dab984fc1c))

## v0.2.9 (2024-07-16)

### Feature

* feat: Add timestamp for modification

Adds a timestamp to the modification date of a note, ensuring accurate tracking of note changes. This resolves an issue where the modification date was not being properly updated. ([`cdc27ab`](https://github.com/RedAtman/simplenote/commit/cdc27abfdcd387311f57a11bad5cadcc76f77d8f))

* feat: Remove Red-Black Tree implementation

The Red-Black Tree implementation has been removed due to its unused status and the potential for future conflicts. This decision streamlines the codebase and reduces maintenance overhead. ([`e4086e0`](https://github.com/RedAtman/simplenote/commit/e4086e0d05b5e0a9802dcbee9def9e309665bf9d))

* feat: Implement Red-Black Tree

Introduces a Red-Black Tree data structure, providing a balanced binary search tree implementation with efficient insertion, deletion, and search operations. Comprehensive unit tests are included to ensure correctness and robustness. ([`7ac1630`](https://github.com/RedAtman/simplenote/commit/7ac163014ae748347949d021009aa0a2c71738c0))

* feat: Implement note modification date tracking using a Red-Black Tree

This commit introduces a new data structure, a Red-Black Tree, to efficiently track the modification date of notes.

The Red-Black Tree stores notes keyed by their modification dates, enabling fast retrieval and deletion of notes based on their modification times. This optimization ensures that when a note&#39;s content or other attributes are modified, the associated modification date is updated correctly and efficiently in the tree.

The modification date is now automatically updated when the `d` attribute of a note is modified, ensuring that the tree always reflects the latest state of notes.

This implementation simplifies note modification handling and provides a performant way to access notes based on their modification date. ([`3d1dff3`](https://github.com/RedAtman/simplenote/commit/3d1dff316a9705a588542ef2bb4d377a1266a22d))

* feat: introduce enum for node colors

Refactor the `Color` enum into the codebase to improve readability and type safety. This enhances the overall maintainability and clarity of the red-black tree implementation. ([`b523da3`](https://github.com/RedAtman/simplenote/commit/b523da37fa658f280a67f17a6f051338408d3a89))

### Fix

* fix: Migrate cache to sublime cache path

Move the note cache file from the package path to the Sublime Text cache path. This helps avoid cluttering the package path with potentially large cache files and ensures consistent cache location across installations. ([`343ba0f`](https://github.com/RedAtman/simplenote/commit/343ba0f419a4bbf6653d9a84146ac865646dac99))

### Refactor

* refactor: Migrate from ID-based note lookups to tree-based

Migrate from storing notes in a dictionary keyed by ID to using a tree structure. This simplifies note retrieval and eliminates the need to maintain a separate dictionary. ([`6fb16cf`](https://github.com/RedAtman/simplenote/commit/6fb16cf16960e4dd8b61b615e0b73de01166229f))

### Test

* test: Implement modificationDate in Note class

Improves the `Note` class by using `modificationDate` for object identification and tree traversal. This eliminates the need for additional unique identifiers and improves data consistency.

The change addresses issues related to duplicated notes and ensures that the tree structure accurately represents the note order based on their modification timestamps. ([`1730335`](https://github.com/RedAtman/simplenote/commit/173033500b7195393429423eccc762ce8d9e1b18))

* test: Add note tree and improve Note class

Added a tree structure to track and access notes more efficiently. This enables unique identification and retrieval of notes. Enhanced the Note class for better data handling and consistency. ([`b2f459d`](https://github.com/RedAtman/simplenote/commit/b2f459df12925f68ea38d1369ced9830958a7e36))

### Unknown

* Merge pull request #3 from RedAtman/fix_cache_file_path

Fix cache file path ([`e424d1e`](https://github.com/RedAtman/simplenote/commit/e424d1ed0974b1aee5eeaa96a16e47bcf40f2b2d))

* Refactor: Store notes in dedicated directory

Moved note storage from a temporary directory to a dedicated &#34;notes&#34; directory within the package. This ensures notes are kept organized and avoids potential conflicts with temporary files. ([`c5cf602`](https://github.com/RedAtman/simplenote/commit/c5cf602a8ea103a985e34c1eab06aa3d1d085314))

* Merge pull request #2 from RedAtman/dev

Dev ([`2e5cac8`](https://github.com/RedAtman/simplenote/commit/2e5cac85eec39c6e4384a139d25b5bcdd405f240))

* Fix: Generate UUID for note_id when missing

When creating a note without a `note_id` provided, generate a random UUID instead of raising an error. This prevents crashes and allows for seamless note creation without requiring manual ID assignment. ([`b8d3dac`](https://github.com/RedAtman/simplenote/commit/b8d3dace3de9e3ff6c6e4be593faced1cd0adb5d))

* Refactor: Replace RedBlackTree implementation

The RedBlackTree implementation has been replaced with a more streamlined version using a dedicated `redblacktree` module. This simplification improves code readability and maintainability, while ensuring proper tree functionality. ([`1cc0bcd`](https://github.com/RedAtman/simplenote/commit/1cc0bcd9a101416ee6de1b2cdd4e0a8a9dd07b71))

* Fix: Properly nest dictionaries for note creation and modification

The code previously incorrectly nested dictionaries when creating and modifying notes, leading to data inconsistencies. This commit fixes this by using a nested dictionary approach for all note interactions, ensuring correct data serialization and retrieval. This change improves the reliability and accuracy of note management within the application. ([`794b1e3`](https://github.com/RedAtman/simplenote/commit/794b1e3e3b110c28126b0411e9f3335033550b0d))

* Fix: Lazy loading of Emmet settings

Avoids unnecessary import of `sublime` module when Emmet settings are not accessed. This enhances performance by delaying the import until it&#39;s actually required. ([`053cbab`](https://github.com/RedAtman/simplenote/commit/053cbabdb4413985a7acde1c4e78c646e2e7cbe3))

## v0.2.8 (2024-07-13)

### Feature

* feat: refactor settings logic, replace hardcoded credentials with environment variables

This change introduces environment variables for app ID, app key, and bucket, allowing users to configure them instead of using hardcoded values. The existing code has been updated to utilize these environment variables, making it more flexible and secure. ([`f6d8972`](https://github.com/RedAtman/simplenote/commit/f6d8972fbee4d5fd8f8bb485e97621f24a1adb23))

* feat: add decorator utils

Adds utility functions for timing function execution, creating class properties, and ensuring singleton instances. These decorators enhance code clarity and maintainability by encapsulating common patterns. ([`328b1cf`](https://github.com/RedAtman/simplenote/commit/328b1cf55c86aa8e818c1d5456976a70defd0a12))

* feat: utils.request: Improve error handling in network requests, And support for content encoding

More comprehensive logging of network request errors, including headers and data, for easier debugging. Additionally, a more robust error handling mechanism is in place to better identify and categorize various network request exceptions. This ensures more informative feedback and graceful error handling in the face of network issues. ([`bfb861b`](https://github.com/RedAtman/simplenote/commit/bfb861bb5d138019df832dcbadf0a9ed05e1ea1a))

### Test

* test: Add Singleton subclassing test ([`48bea8b`](https://github.com/RedAtman/simplenote/commit/48bea8bcaacdfb63c46952e18346b89fd9c5ac7b))

### Unknown

* Merge pull request #1 from RedAtman/dev

refactor: refactor settings logic ([`aca1b37`](https://github.com/RedAtman/simplenote/commit/aca1b373531222ba06e4efad6ca8e7ddf60a1807))

## v0.2.7 (2024-07-12)

### Chore

* chore: Clean up useless code ([`1be63db`](https://github.com/RedAtman/simplenote/commit/1be63dbe42ed54c37c5bf540b47b719055c60479))

* chore: remove old simplenote api ([`8bcf1b0`](https://github.com/RedAtman/simplenote/commit/8bcf1b00622d4935e22ebb33ec39a9e6fc8d9f75))

* chore: Remove unused code and dataclass definitions in api.py ([`1a59cd5`](https://github.com/RedAtman/simplenote/commit/1a59cd577f9e0ae0c2cd8645e1bf0b389b4f3eaf))

### Feature

* feat: Add Simplenote settings file

Adds a new settings file for configuring the Simplenote plugin, allowing users to customize credentials, sync behavior, and other preferences.  This enables users to tailor the plugin to their specific needs and workflow. ([`f66e19b`](https://github.com/RedAtman/simplenote/commit/f66e19be6865007a8f74b939f0e5edfc8567d92e))

* feat: outline future development plans

Adds a section to the README outlining planned features for the future. ([`90e72f5`](https://github.com/RedAtman/simplenote/commit/90e72f52179c70d03cc84068377e58d5e54a080a))

* feat: Implement Red-Black Tree

Adds a Red-Black Tree implementation with support for insertion, deletion, and basic search operations. The implementation is based on classic algorithms and adheres to Red-Black Tree invariants. Includes unit tests for verification. ([`b498f9c`](https://github.com/RedAtman/simplenote/commit/b498f9cb580df113e187e2f0c23861f7be79dae7))

* feat: Remove SimplenoteManager dependency

Refactored code to remove the SimplenoteManager singleton and its associated dependencies. This simplifies the project structure and eliminates unnecessary state management.  The `Local` class now directly handles data interaction. ([`9777393`](https://github.com/RedAtman/simplenote/commit/97773930f5e9d62b5877517087556b5078b4fc2f))

* feat: Cleanup temporary files

Removes orphaned temporary files on plugin load, ensuring consistency between cached notes and actual files.
This prevents potential issues with outdated or missing files and improves overall plugin stability. ([`6968f22`](https://github.com/RedAtman/simplenote/commit/6968f2250a892dd4c9f9dbcc2c045284f26eeaf3))

* feat: Remove unnecessary logging

Removed unnecessary logging statements to improve code cleanliness and performance. The code now focuses solely on essential functionality. ([`b34026f`](https://github.com/RedAtman/simplenote/commit/b34026f71921693485a1c2625edf976d2531d3b5))

* feat: Streamline logging in operations

Remove unnecessary logging statements that were providing duplicate information and don&#39;t contribute to the core functionality. This reduces code complexity and enhances readability. ([`3e8b92e`](https://github.com/RedAtman/simplenote/commit/3e8b92e211935df6a45410d62c41a8780c44a80b))

* feat: Remove unnecessary attributes from Note model

Removed redundant `modifydate` and `systemtags` attributes from the `Note` model as they were just mirrored from the underlying `_Note` data structure. This simplifies the model and reduces code duplication. ([`566a0e9`](https://github.com/RedAtman/simplenote/commit/566a0e9e106a217f7b68419da3555c3f41b368eb))

* feat: remove view-related logic from note objects

Removed unnecessary view-related logic from note objects. This simplifies the codebase and improves overall structure. The view is now only handled when a note is opened or edited, not stored as part of the Note object itself. ([`20d71da`](https://github.com/RedAtman/simplenote/commit/20d71daf1bfd7a800e5670b67bab38d947b80d80))

* feat: Refine note finding logic

Adds a `TODO` to address the potential for multiple matching notes. This change enhances the accuracy and clarity of note retrieval by leveraging regular expressions for more precise pattern matching. ([`0ba6b2a`](https://github.com/RedAtman/simplenote/commit/0ba6b2a1dfc0f131d4e608f0b13ed882692323cf))

* feat: Improve note management and syncing

Simplify note management and syncing by using callback functions instead of complex merge logic. Remove unnecessary functions and optimize code for improved readability and efficiency. ([`85d0929`](https://github.com/RedAtman/simplenote/commit/85d0929d5121359af5004be55184f255a301fa53))

* feat: Implement note content persistence and file management ([`c06b222`](https://github.com/RedAtman/simplenote/commit/c06b222e848a89e7063a83cd25bbd8b02a8aec5c))

* feat: settings.Settings ([`616c9e3`](https://github.com/RedAtman/simplenote/commit/616c9e3cb9f3c98ffe828ffe002677a5126deeb7))

* feat: model.Note.mapper_id_note ([`2b2cbf3`](https://github.com/RedAtman/simplenote/commit/2b2cbf382883803929f9b7cf35bbe7749840cee3))

* feat: Add msg to the api return value ([`51012a0`](https://github.com/RedAtman/simplenote/commit/51012a0aeaf9cee33ba51c15174c4958fa505557))

* feat: utils.tools.py ([`b9a3461`](https://github.com/RedAtman/simplenote/commit/b9a3461065e0d7076cff59305fb30868d2a165ab))

* feat: models.py ([`7aa2fdf`](https://github.com/RedAtman/simplenote/commit/7aa2fdf4f3d673a261097e81a1118f1bc85eb979))

* feat: add the new api.Simplenote ([`a8a1831`](https://github.com/RedAtman/simplenote/commit/a8a1831ae04b7a8e84873337413572cf80b1f248))

* feat: first commit ([`c269695`](https://github.com/RedAtman/simplenote/commit/c269695c81257341a053b557c35fc9b1af8809da))

### Fix

* fix: config.py ([`48e3d1b`](https://github.com/RedAtman/simplenote/commit/48e3d1b178fe89a95c36f703b32fe0c7724e14f8))

* fix: fix settings load &amp; fix several method bug for api.Simplenote ([`7df59b3`](https://github.com/RedAtman/simplenote/commit/7df59b3b85ddeb18cafb66a44d64f56b80c1ab8d))

### Performance

* perf: utils.request.py ([`603d15a`](https://github.com/RedAtman/simplenote/commit/603d15aa8c2bf719512b55d4f5801bb70ed1c3c4))

### Refactor

* refactor: open_view, close_view ([`98c62bc`](https://github.com/RedAtman/simplenote/commit/98c62bc8dcf7d0bc8da79bbeca2ff8bce3dfd519))

* refactor: utils.logger ([`97a570e`](https://github.com/RedAtman/simplenote/commit/97a570e3f5a6f9d8fa6a63c8ae62504d28c963fc))

* refactor: Unify naming simplenote variables &amp; decouple from config.py ([`21da7b6`](https://github.com/RedAtman/simplenote/commit/21da7b61a079ea1bbb106bf3a6af065fb49a030c))

* refactor: adjust model struct ([`1cafde3`](https://github.com/RedAtman/simplenote/commit/1cafde30a3309945765a865677ee4f8d44ebbfd6))

* refactor: instead old api with new api &amp; model ([`5da5e88`](https://github.com/RedAtman/simplenote/commit/5da5e88ac19fecc95a3c8b3522b039f85bd60004))

* refactor: Refactor Simplenote operations for better code structure and compatibility with new simplenote api ([`5d10c74`](https://github.com/RedAtman/simplenote/commit/5d10c740a5b7372d0258d8bfd1d7417c9666ce1f))

* refactor: Add logger output and handler classes ([`dc29712`](https://github.com/RedAtman/simplenote/commit/dc2971297eea13353a65955d5e59058afb3ce80c))

* refactor: Optimize code structure ([`5249417`](https://github.com/RedAtman/simplenote/commit/5249417847fe442e4ba64444948eb079d87ae323))

### Test

* test: Add settings tests

Adds unit tests for the `Settings` class to ensure proper functionality and type checking. This helps maintain code quality and provides confidence in the settings handling within the application. ([`15ecfc8`](https://github.com/RedAtman/simplenote/commit/15ecfc8d8fb111a05c7b9333be5ac160b2d1ec8a))

* test: Remove unnecessary fields from note object

The `shareURL`, `publishURL`, `modificationDate`, and `creationDate` fields were not being used in the tests and are now removed to simplify the test setup. ([`e229059`](https://github.com/RedAtman/simplenote/commit/e2290594c851bd7d89b81050221c8807c9e2273d))

* test: Improve API Testing and Refactor

Refactor the API testing setup to utilize a random note ID for testing purposes. This enhances the robustness of the tests by mitigating potential issues arising from using the same note ID repeatedly. Additionally, the code now includes more detailed assertions for verifying the API responses. These changes ensure more comprehensive coverage and stability in the testing suite. ([`2a94d27`](https://github.com/RedAtman/simplenote/commit/2a94d279143a03f59d7b35c15d802183aa1c302f))

* test: add content field and update file naming

Adds a `_content` field to the `Note` class for storing note content and updates the `_filename` attribute to reflect the actual content instead of the title. This change ensures that note filenames are more descriptive and accurately represent the content of the note.

Also, updates the `test_mapper_id_note` test to cover these changes and includes a new test to validate the `_content` field functionality. ([`c4902b9`](https://github.com/RedAtman/simplenote/commit/c4902b99a7e12e51562d22a7c65e61f5aa0c6a59))

* test: model.Note ([`cbb4902`](https://github.com/RedAtman/simplenote/commit/cbb4902a7e877882ffd856726f713a28d48fd944))

* test: Improve Simplenote API tests ([`e541070`](https://github.com/RedAtman/simplenote/commit/e541070f14a8f9456a1f695a50a90c4e7d2c1140))

### Unknown

* Fix: Robust autosave handling

The autosave logic has been made more robust by adding checks for invalid types. This ensures that the autosave functionality handles potential edge cases more reliably.  The changes also improve code clarity by simplifying the structure of the code related to autosave. ([`7ceff57`](https://github.com/RedAtman/simplenote/commit/7ceff574130cde4c098382ad1579d89355fa0767))

* Refactor: Remove unnecessary imports

Removed unused imports from `api.py` to streamline the code and improve readability. ([`f754b3c`](https://github.com/RedAtman/simplenote/commit/f754b3c409f965f70d31ea94811475368ed387c2))

* Fix: Remove unnecessary modification date updates

Removed unnecessary updates to the `modificationDate` field in the `Note` model, simplifying the code and improving its accuracy. The modification date is now handled automatically by the Simplenote API during modifications. ([`8e2ced1`](https://github.com/RedAtman/simplenote/commit/8e2ced1dcd409fbbf3c1647795bfadb012877b75))

* Fix: Prevent deletion of non-existent notes

Ensure that `NoteDeleter` is only initialized with a valid `Note` object. This prevents the deletion of non-existent notes and ensures the command&#39;s integrity. ([`bacf51c`](https://github.com/RedAtman/simplenote/commit/bacf51c3ef295ea7aa910337cbbb769bc7a78324))

* Fix: Handle potential errors during file deletion and note retrieval

Enhanced error handling during file deletion and note retrieval to improve robustness.  The changes address potential `OSError` and `FileNotFoundError` during file deletion and handle cases where a note with a given ID might not exist. This ensures smoother operation and helps prevent unexpected program termination. ([`48a80a0`](https://github.com/RedAtman/simplenote/commit/48a80a09ad40011ec8265a78329daa32db62fb13))

* Fix: Improve note syncing and syntax handling

Refined note syncing logic, addressing potential issues with note updates and syntax settings. The updated code ensures proper handling of notes with tags and system tags, improving the consistency and reliability of note syncing. Also, the syntax setting is now applied more robustly, enhancing the user experience. ([`a99cd6c`](https://github.com/RedAtman/simplenote/commit/a99cd6c301c707aeffbc6f49640e006945062201))

* Refactor: Move note loading to a separate function

The note loading logic has been moved out of the `Local` class and into a separate function `load_notes`. This improves code organization and makes it easier to reuse the loading logic in other parts of the application.

The `Note.mapper_id_note` dictionary is now used to store and load notes instead of the `Local.objects` list. This provides a more efficient and flexible approach to managing notes. ([`9e7659a`](https://github.com/RedAtman/simplenote/commit/9e7659af5d2165365ac15f61e6c5412d77950466))

* Fix: Prevent unnecessary note syncing

The previous implementation would attempt to sync notes even if they were unchanged. This commit adds a check to avoid unnecessary syncs when the note&#39;s content hasn&#39;t been modified. ([`00f6aef`](https://github.com/RedAtman/simplenote/commit/00f6aef660ed1cd36e328ab7a822d9df9207d2e5))

* Fix: Remove unnecessary settings loading in `HandleNoteViewCommand`

Removed redundant loading of settings within `HandleNoteViewCommand`. The settings were already loaded elsewhere and didn&#39;t need to be loaded again within this class. This simplifies the code and improves efficiency. ([`b482393`](https://github.com/RedAtman/simplenote/commit/b4823934621b0db4593502cb4812cf6d2f14ed9c))

* Fix: Improve logging and simplify sync logic

Remove unnecessary checks and improve logging messages for clearer debugging. Simplify the sync logic to avoid redundant checks and operations. ([`d141ec5`](https://github.com/RedAtman/simplenote/commit/d141ec51be6d962583fedfe4283c15c831563a09))

* Fix: Ensure note view is passed correctly to NoteDeleter

Update the `NoteDeleteCommand` to correctly pass the `note_view` to the `NoteDeleter` callback, ensuring proper deletion handling. ([`ca4bfb9`](https://github.com/RedAtman/simplenote/commit/ca4bfb9b196a9981a8ba2fd1cb6f205b9f8a042b))

* Fix: Remove unnecessary flush logic and simplify Note initialization

Removed the unnecessary flush logic in the Note class, as it was redundant and caused issues. Also simplified the initialization process by using a default value for the `content` field and by removing unused code. These changes improve the efficiency and maintainability of the code. ([`b5b4ba5`](https://github.com/RedAtman/simplenote/commit/b5b4ba58babb1806efec5bed6d6de533cfa437de))

* Fix: Unnecessary assertion and potential issue

Removed an unnecessary assertion and marked a potential issue with `# TODO`.

This ensures cleaner code and prevents potential issues with the code. ([`e2cfdac`](https://github.com/RedAtman/simplenote/commit/e2cfdac8c686b61e176fac83d6cf541e21b58ec2))

* Fix: Handle note changes more reliably

Refactor the way note changes are handled to ensure updates are applied consistently and efficiently.
- The `on_note_changed` function now operates directly on the note object, removing the need to pass a view explicitly.
- Improved handling of open and closed notes, ensuring that updates are reflected in the correct view and that closed views are handled properly.
- Removed unnecessary calls to `sublime.set_timeout` in `on_note_changed`.

This addresses issues where note updates were not being applied correctly, particularly when a note was open in multiple views or closed while being modified. ([`55c7a9d`](https://github.com/RedAtman/simplenote/commit/55c7a9d1e34827c94f2a94c2bae251787777a6b1))

* Fix: Remove unnecessary mapper and improve performance

Removed unnecessary `mapper_path_note` and `mapper_id_note` from the `Note` class. This improves performance and reduces unnecessary memory overhead. Additionally, streamlined the `Note` class by using `repr=False` for fields that don&#39;t need to be included in the object&#39;s representation. ([`350e915`](https://github.com/RedAtman/simplenote/commit/350e915395b07455c9678067a49badea41603896))

* Fix: Note._content ([`3b3d90f`](https://github.com/RedAtman/simplenote/commit/3b3d90ff15f73af9e069404f832c6339317e7594))

* Fix: Improve Note List Command User Experience

Renamed `handle_selected` to `on_select` to reflect its purpose.
Added placeholder text to the Quick Panel for clarity.
This makes the note list command more user-friendly. ([`50b3808`](https://github.com/RedAtman/simplenote/commit/50b38081f6e2ceef14e6adde396c7dabbd01297a))

* Refactor: Move method get_note_from_filepath to Note class

Moved the logic for retrieving a note from a file path to the Note class, removing redundant code in `simplenote.py` and `simplenotecommands.py`. This improves code organization and reduces redundancy. ([`2c84539`](https://github.com/RedAtman/simplenote/commit/2c84539cf6b8f9112ee2bba372ee7f1f34cea594))

* Fix: Prevent unnecessary note syncs on file save

Removed the check that compares the current content of the view to the note content when the view is saved. This was causing unnecessary syncing when the user made no changes to the note. This optimization prevents unnecessary syncing and improves performance. ([`18d0988`](https://github.com/RedAtman/simplenote/commit/18d0988520dbab0670c69ecbe71ee16460592630))

* Fix: Remove unnecessary import and model dependency

Removed an unused import and dependency on the `Note` model from `sublime.py`. This change streamlines the code and improves maintainability. ([`c6609bd`](https://github.com/RedAtman/simplenote/commit/c6609bd525ff401fca668529b4bf43cc270bdb5b))

* Fix: Resolve filename sync issues with note updates ([`012dd20`](https://github.com/RedAtman/simplenote/commit/012dd206d99d0bb293c953eb70a15d7109ef32f2))

* Fix: Simplenote API token loading ([`d3a56f5`](https://github.com/RedAtman/simplenote/commit/d3a56f5542787888e1bee629b7f86c7549b0a78e))

* Refactor: Rearrange operation classes

Reorder classes in `operations.py` to improve logical grouping and maintain consistency with the overall project structure.  This enhances code readability and maintainability. ([`408c9c4`](https://github.com/RedAtman/simplenote/commit/408c9c4c2cb917ffa8f3f7f18143983a9c805a2c))

* refacotr: relink several method to model.Note ([`8cfddb4`](https://github.com/RedAtman/simplenote/commit/8cfddb414fca4922775ac96f7b156a7cdf0885de))

* pref: refine API init ([`1dc589e`](https://github.com/RedAtman/simplenote/commit/1dc589ede226040a32650f91af170969bff9bee7))

* pref: logger level ([`bf4f2af`](https://github.com/RedAtman/simplenote/commit/bf4f2af32c2959319a515500baecbf53e6f56eb3))

* doc: update README.md ([`ea542ed`](https://github.com/RedAtman/simplenote/commit/ea542ed161451234548a2933b20754873da1c8d7))

* pref: rename several command ([`4b02583`](https://github.com/RedAtman/simplenote/commit/4b025834951b8bafe4a9a493d630b9ce9b64d8d4))

* pref: rename several operation ([`fc4c4ba`](https://github.com/RedAtman/simplenote/commit/fc4c4baa5febfd34c658fc01e9df9448766cb752))

* misc: ([`c5510e9`](https://github.com/RedAtman/simplenote/commit/c5510e9ff0a8896033b166e30054181a5fb26212))

* pref: refine logger level ([`bfc582c`](https://github.com/RedAtman/simplenote/commit/bfc582c34d394395775ba7c9989456666048a028))

* refact: model.py ([`b1c905c`](https://github.com/RedAtman/simplenote/commit/b1c905c1db1626d81ab0d684e4e40a3f22290dfa))

* misc: rename config.py to _config.py ([`af5508b`](https://github.com/RedAtman/simplenote/commit/af5508b711af7c5ca1c6e85541b31ff92d54d209))

* misc: Update pygments dependency in dependencies.json ([`87b74b1`](https://github.com/RedAtman/simplenote/commit/87b74b1a836b4c16917df3690bf3e70752bbd9f6))

* misc: refine simplenote.py import ([`6a4091c`](https://github.com/RedAtman/simplenote/commit/6a4091c1e49e5afb62539301bc9f8967534c15e6))
