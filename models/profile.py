from typing import Any, Dict

class Experience:
    """
    A class to represent a single experience entry.
    """
    def __init__(self, position_title="N/A", institution_name="N/A", linkedin_url="N/A", 
                 from_date="N/A", to_date="N/A", duration="N/A", 
                 location="N/A", description="N/A", skills="N/A"):
        self.data = {
            "position_title": position_title,
            "institution_name": institution_name,
            "linkedin_url": linkedin_url,
            "from_date": from_date,
            "to_date": to_date,
            "duration": duration,
            "location": location,
            "description": description,
            "skills": skills,
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the experience to a dictionary.
        """
        return self.data

class Education:
    """
    A class to represent a single education entry.
    """
    def __init__(self, institution_name="N/A", degree="N/A", linkedin_url="N/A", 
                 from_date="N/A", to_date="N/A", description="N/A", skills="N/A"):
        self.data = {
            "institution_name": institution_name,
            "degree": degree,
            "linkedin_url": linkedin_url,
            "from_date": from_date,
            "to_date": to_date,
            "description": description,
            "skills": skills,
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the education to a dictionary.
        """
        return self.data

class Project:
    """
    A class to represent a single project entry.
    """
    def __init__(self, project_name="N/A", from_date="N/A", to_date="N/A", 
                 institution_name="N/A", description="N/A", skills="N/A"):
        self.data = {
            "project_name": project_name,
            "from_date": from_date,
            "to_date": to_date,
            "institution_name": institution_name,
            "description": description,
            "skills": skills,
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the project to a dictionary.
        """
        return self.data

class Certificate:
    """
    A class to represent a single certificate entry.
    """
    def __init__(self, certificate_name="N/A", cert_date="N/A", 
                 institution_name="N/A", skills="N/A"):
        self.data = {
            "certificate_name": certificate_name,
            "institution_name": institution_name,
            "cert_date": cert_date,
            "skills": skills,
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the certificate to a dictionary.
        """
        return self.data

class Honor:
    """
    A class to represent a single honor entry.
    """
    def __init__(self, honor_name="N/A", institution_name="N/A"):
        self.data = {
            "honor_name": honor_name,
            "institution_name": institution_name,
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the honor to a dictionary.
        """
        return self.data

class Language:
    """
    A class to represent a language and its proficiency.
    """
    def __init__(self, language_name="N/A", proficiency="N/A"):
        self.data = {
            "language_name": language_name,
            "proficiency": proficiency,
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the language to a dictionary.
        """
        return self.data

class Publication:
    """
    A class to represent a publication entry.
    """
    def __init__(self, publication_name="N/A", institution_name="N/A", publication_url="N/A"):
        self.data = {
            "publication_name": publication_name,
            "institution_name": institution_name,
            "publication_url": publication_url
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the publication to a dictionary.
        """
        return self.data
    
class Profile:
    """
    A class to represent a user profile with default values.
    """
    def __init__(self, url="N/A"):
        """
        Initialize a Profile instance with default values.
        """
        self.data = {
            "linkedin_url": url,
            "name": "N/A",
            "location": "N/A",
            "job_title": "N/A",
            "about": "N/A",
            "experiences": [],  
            "educations": [],   
            "projects": [],     
            "certificates": [], 
            "honors": [],       
            "languages": [],    
            "publications": [],
            "skills": [],       
        }

    def set_field(self, field_name: str, value: Any) -> None:
        """
        Set a specific field in the profile.

        Args:
            field_name (str): The name of the field to set.
            value (Any): The value to assign to the field.

        Raises:
            KeyError: If the field name does not exist.
        """
        if field_name not in self.data:
            raise KeyError(f"Field '{field_name}' is not valid.")
        self.data[field_name] = value

    def add_experience(self, experience: Experience) -> None:
        """
        Add an experience object to the profile.

        Args:
            experience (Experience): An instance of Experience.
        """
        self.data["experiences"].append(experience.to_dict())

    def add_education(self, education: Education) -> None:
        """
        Add an education object to the profile.

        Args:
            education (Education): An instance of Education.
        """
        self.data["educations"].append(education.to_dict())
    
    def add_project(self, project: Project) -> None:
        """
        Add a project object to the profile.

        Args:
            project (Project): An instance of Project.
        """
        self.data["projects"].append(project.to_dict()) 
    
    def add_certificate(self, certificate: Certificate) -> None:
        """
        Add a certificate object to the profile.

        Args:
            certificate (Certificate): An instance of Certificate.
        """
        self.data["certificates"].append(certificate.to_dict()) 
    
    def add_honor(self, honor: Honor) -> None:
        """
        Add a honor object to the profile.

        Args:
            honor (Honor): An instance of Honor.
        """
        self.data["honors"].append(honor.to_dict()) 
    
    def add_publication(self, publication: Publication) -> None:
        """
        Add a publication object to the profile.

        Args:
            publication (Publication): An instance of Publication.
        """
        self.data["publications"].append(publication.to_dict())

    def add_language(self, language: Language) -> None:
        """
        Add a language object to the profile.

        Args:
            language (Language): An instance of Language.
        """
        self.data["languages"].append(language.to_dict())

    def add_skill(self, skill: str) -> None:
        """
        Add a skill to the profile.

        Args:
            skill (str): A skill to add.
        """
        self.data["skills"].append(skill)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the profile data to a dictionary.

        Returns:
            Dict[str, Any]: The profile data as a dictionary.
        """
        return self.data
