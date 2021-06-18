# E707 Electronics Parts Database (E7EPD)
## UNRELEASED Database Rev 0.1, CLI Rev 0.2
## Still a Work-In-Progress, so is the name

This project attempts to create yet another open-source electronics parts management system. While there are some out
there, I wasn't satisfied with them.

## Philosophy and Goals
- Simplicity: The core application should remain simple to allow for ease of adding features. This is partially
  why only a CLI will be created for this instead of a webpage or a GUI application, and why the language this proogram
  will use is Python.
- Modularity: The core application will be made in such a way as to allow ease of adding new parameters for example.
  Mostly will be accomplished with configuration lists
- Parameterization, Kind of: The only components that really need parameterization are  things like resistors, capacitors, etc.
  Things where the specific part number doesn't matter for a project. 
  In contrast to a microcontroller, a project can't really say: I don't care which micro as long as it's 8-bits.
- Interoperability: This database specification will use a common database (MySQL/SQLite), and be documented so that
  migration from and away from this specific program shall be possible.
  
## Security:
As this project directly places variables into SQL commands, this project is vulnrable to sql injection attacks. 
This is meant to be used as a personal database, so security is not really that big a conern.
#### TL;DR: THIS PROJECT IS VULNERABLE TO SQL INJECTIONS, THUS DO NOT USE THIS IN A PRODUCTION ENVIRONMENT.

## Docs
The documentation for this project can be found in [the project's readthedocs](https://e7epd.readthedocs.io/en/latest/).

The documentation is still a work-in-progress

## Database specification and Interface
For more details as to how parts are stored in the database, see [DATABASE_SPEC.md](DATABASE_SPEC.md)

The python file `e7epd.py` includes a `E7EPD` class, which is a wrapper around the database.
To run the `e7epd.py`, you will need Python>3.7 with their pre-installed packages.

## CLI Application
To start using this application/database, simply launch `cli.py`. Prompts should show up, allowing you to do the following basic tasks per component type:
- Add a part
- Delete a part
- See the entire part's database table
More features and interactions for the CLI will be added in Rev 0.1
  
The following packages are required to run it:
- [rich](https://pypi.org/project/rich/)
- [engineering_notation](https://pypi.org/project/engineering-notation/)
- [questionary](https://pypi.org/project/questionary/)

## TODO: Database specification
### Rev 0.1 TODO:
- [ ] Create examples of how to interact with the `E7EPD` class.
- [ ] Add method of handling database migration.

### Rev 0.2 and future TODO:
- [ ] Create a projects specification, including for generic parts.
- [ ] Allow a mySQL database connection

## TODO: CLI Application
- [ ] Allow for more user tasks, like only showing filtered parts.
- [x] Allow for fractional input (like 1/4 for things like power rating)
- [ ] Using the `digikey-api` python package or other electronics distributor's API, allow for automatic part lookup
  thru the manufacturer part number and import characteristics for said part.