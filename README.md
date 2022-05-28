# E707 Electronics Parts Database (E7EPD)
## Database Rev 0.5, Backend and CLI Rev 0.5
## Still a Work-In-Progress

This project attempts to create yet another open-source electronics parts management system. While there are some out
there, I wasn't satisfied with them.

## Philosophy and Goals
- Simplicity: The core application should remain simple to allow for ease of adding features. This is partially
  why only a CLI will be created for this instead of a webpage or a GUI application, and why the language this program
  will use is Python.
- Modularity: The core application will be made in such a way as to allow ease of adding new parameters for example.
  Mostly will be accomplished with configuration lists
- Parameterization, Kind of: The only components that really need parameterization are things like resistors, capacitors, etc.
  Things where the specific part number doesn't matter for a project. 
  In contrast to a microcontroller, a project can't really say: I don't care which micro as long as it's 8-bits.
- Interoperability: This database specification will use a common database (SQL like), and be documented so that
  migration from and away from this specific program shall be possible.

## Installation
From Rev0.4 and onwards, `e7epd` can be installed with
```
pip install e7epd
```
To install from the GitHub repository, run the following command inside the cloned repository:
```
pip install .
```
  
## Security:
As of Rev 0.3, this project uses sqlAlchemy, without directly creating SQL commands like before. This should make it more
secure than previous revisions in terms of arbitrary SQL code issues.
#### NOTICE: The password for a mySQL user is stored in a json file in plain format. Make sure the mySQL account only has permission to the parts' database.

## CLI Application
To start using this application/database, simply launch `e7epd` from the command line. Prompts should show up, allowing you to interact with the 
parts database. Some of the things you can do with it are:
- Add a part
- Delete a part
- See the entire part's database table
- Add and/or remove stock to a part

## Docs
The documentation for this project can be found in [the project's readthedocs](https://e7epd.readthedocs.io/).

The documentation is for the latest released version. For the non-released master docs, see [here](https://e7epd.readthedocs.io/en/latest/).

## Database specification and Interface
For more details as to how parts are stored in the database, see [database specification](https://e7epd.readthedocs.io/en/latest/database_spec.html)

The python file `e7epd.py` includes a `E7EPD` class, which is a wrapper for the database.
To add the database wrapper `e7epd.py` to your project, you will need Python>3.7 with their pre-installed packages as well as the following extra packages:
- [SQLAlchemy](https://pypi.org/project/SQLAlchemy/)
- [alembic](https://pypi.org/project/alembic/)
  
The following packages are required to run it:
- [rich](https://pypi.org/project/rich/)
- [engineering_notation](https://pypi.org/project/engineering-notation/)
- [questionary](https://pypi.org/project/questionary/)
- [SQLAlchemy](https://pypi.org/project/SQLAlchemy/)
- [alembic](https://pypi.org/project/alembic/)

## Changelog and In-Progress
For the changelog and in-progress additions, see [the project's master changelog](https://e7epd.readthedocs.io/en/latest/changelog.html) for more details on that.

## License

The license for this project is the GNU General Public License v3. The full text can be found at [LICENSE.md](LICENSE.md)
