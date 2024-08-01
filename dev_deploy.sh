# local development deploy
zip -r Simplenote.sublime-package . -x ".git/*" ".github/*" ".gitignore" ".idea/*" ".vscode/*" ".pytest_cache/*" "pyproject.toml" "package-lock.json" "package.json" "node_modules/*" ".env.*" ".DS_Store" "assets/*" "*__pycache__/*" "tmp/*" "tests/*" "logs/*" "sublime_api.py" "dev_deploy.sh" "package-metadata.json"

mv Simplenote.sublime-package $HOME/Library/Application\ Support/Sublime\ Text/Installed\ Packages/Simplenote.sublime-package
