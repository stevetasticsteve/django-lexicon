import subprocess
import tempfile


def unmunch(dic_content: str, aff_content: str) -> list:
    """Generate words from Hunspell .dic and .aff contents using the unmunch command.

    Args:
        dic_content: The string content of the dictionary file (.dic).
        aff_content: The string content of the affix file (.aff).

    Returns:
        A string containing the unmunch output.

    Raises:
        subprocess.CalledProcessError: If the unmunch command fails.
    """
    # Ensure dictionary content has a valid length header
    dic_content = check_length_dic_contents(dic_content)

    # Create temporary files for the .dic and .aff data
    with (
        tempfile.NamedTemporaryFile(mode="w+", delete=True) as dic_temp,
        tempfile.NamedTemporaryFile(mode="w+", delete=True) as aff_temp,
    ):
        # Write the contents to the temp files
        dic_temp.write(dic_content)
        aff_temp.write(aff_content)

        # Flush to ensure data is written
        dic_temp.flush()
        aff_temp.flush()

        # Call the unmunch command using the temporary files
        result = subprocess.run(
            ["unmunch", dic_temp.name, aff_temp.name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,  # Capture errors for debugging if needed
            text=True,  # Automatically decode stdout/stderr to strings
        )

        # Raise an exception if the command fails
        result.check_returncode()

        return result.stdout.strip().splitlines()


def check_length_dic_contents(dic_content: str, default_length: int = 100) -> str:
    """Ensure the provided .dic content has a valid length header.

    Args:
        dic_content: The string content of the dictionary file (.dic).
        default_length: Default length to insert if no length is present.

    Returns:
        The .dic content with a valid length header.
    """
    lines = dic_content.split("\n")

    # Ensure the first line is a valid length header
    if not lines[0].strip().isdigit():
        lines.insert(0, str(default_length))

    return "\n".join(lines)
