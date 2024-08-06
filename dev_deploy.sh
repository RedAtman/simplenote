# local development deploy
dirname=$(basename "$(pwd)" | tr -d '\n')
echo $dirname
package_name=$dirname.sublime-package
echo $package_name

zip -r $package_name . -x ".env*" ".git/*" ".github/*" ".gitignore" ".idea/*" ".vscode/*" ".pytest_cache/*" "pyproject.toml" "package-lock.json" "package.json" "node_modules/*" ".env.*" "*.DS_Store" "assets/*" "*__pycache__/*" "tmp/*" "tests/*" "logs/*" "sublime_api.py" "dev_deploy.sh" "package-metadata.json"

mv $package_name $HOME/Library/Application\ Support/Sublime\ Text/Installed\ Packages/$package_name
