from typing import Any, Dict

class JobDescription:
    """
    A class to represent a job description with default values.
    """

    def __init__(self, url = "N/A", category="N/A", job_title="N/A"):
        """
        Initialize a JobDescription instance with default values.
        """
        self.data = {
            "Category": category,
            "Company Name": "N/A",
            "Company URL": "N/A",
            "Job Title": job_title,
            "Location": "N/A",
            "Date Posted": "N/A",
            "Work Type": "N/A",
            "Time Type": "N/A",
            "Job Level": "N/A",
            "Job Description": "N/A",
            "Job URL": url
        }

    def set_field(self, field_name: str, value: Any) -> None:
        """
        Set a specific field in the job description.

        Args:
            field_name (str): The name of the field to set.
            value (Any): The value to assign to the field.

        Raises:
            KeyError: If the field name does not exist.
        """
        if field_name not in self.data:
            raise KeyError(f"Field '{field_name}' is not valid.")
        self.data[field_name] = value

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the job description data to a dictionary.

        Returns:
            Dict[str, Any]: The job description as a dictionary.
        """
        return self.data