<<<<<<< HEAD
# E-Start-Backend
A faster and easy web backend framework.
=======
# E-Starter

E-Starter is a simple and easy-to-use backend framework designed for small to medium-sized projects. It provides a robust starting point for developers looking to jumpstart their application development without dealing with complex configurations.

### Prerequisites

- Python (Python 3.12 recommended)
- Linux (Ubuntu 20.04 recommended)

## Getting Started

Follow these simple steps to get a local copy up and running.

### Clone the Repository

```bash
git clone https://github.com/Accec/E-Start-Backend
```

### Installation

1. Navigate to the `src` directory:
   ```bash
   cd src
   ```
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Navigate to the `config` directory:
   ```bash
   cd config
   ```
4. Copy the example configuration file and rename it:
   ```bash
   cp example.py <CONFIG_NAME>.py
   ```
5. Open your configuration file with a text editor (like `vi`) and set the configuration:
   ```bash
   vi <CONFIG_NAME>.py
   ```
6. Navigate back to the `src` directory:
   ```bash
   cd ..
   ```
7. Open the `.env` file with a text editor (like `vi`):
   ```bash
   vi .env
   ```
8. Set the mode to development by updating the MODE environment variable:
   ```bash
   MODE=<CONFIG_NAME>
   ```
9. Initialize the database and create an admin user:
   ```bash
   python main.py init_database
   python main.py create_admin --username <USERNAME> --password <PASSWORD>
   ```

Congratulations! Now, you're all set to start using E-Starter for your project.

### Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

### License

Distributed under the MIT License. See `LICENSE` for more information.

### Contact

Github - [@Accec](https://github.com/Accec)

Project Link: [https://github.com/Accec/E-Start-Backend](https://github.com/Accec/E-Start-Backend)
>>>>>>> dev
