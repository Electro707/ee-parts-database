# E707 Electronics Parts Database (E7EPD)
## Still a Work-In-Progress, so is the name

This project attempts to create yet another open-source electronics parts management system. While there are some out
there, I wasn't satisfied with them.

## Philosophy and Goals
- Simplicity: The core application should remain simple to allow for ease of adding features. This is partially
  why only a CLI will be created for this instead of a webpage or a GUI application, and why the language this proogram
  will use is Python.
- Modularity: The core application will be made in such a way as to allow ease of adding new parameters for example.
  Mostly will be accomplished with configuration lists
- Parameterization: This application will allow for parts to contain plenty of parameters (from a resistor's power 
  dissipation to an ADCs sampling rate) to allow for easy sorting
- Generic Parts: This database application will allow for the addition, interaction, and project management with
  parts that don't have a specific manufacturer, as well as allowing for projects to add generic components to their
  BOM.
- Interoperability: This database specification will use a common database (MySQL/SQLite), and be documented so that
  migration from and away from this specific program shall be possible.
  

## Rev 0.1 TODO:
- [ ] Add more basic components like capacitors.
- [ ] Allow the backend to handle generic components in finding if they exist already in the database
- [ ] Add more functions to the `EEData` class
- [ ] Create examples
- [ ] Create a basic CLI application for interacting with parts

# Rev 0.2 TODO:
- [ ] Create a projects specification, including for generic parts
- [ ] Add method of handling database migration
