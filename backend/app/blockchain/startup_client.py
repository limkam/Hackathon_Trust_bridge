import subprocess
import json
from typing import Dict, Any
from pathlib import Path
from app.core.config import settings
from app.utils.logger import logger
from app.utils.helpers import parse_json_response
from app.core.exceptions import BlockchainError


class StartupClient:
    """Python wrapper for Solana startup registry scripts."""
    
    def __init__(self):
        # Resolve path relative to backend directory
        backend_dir = Path(__file__).parent.parent.parent
        scripts_path = (backend_dir / settings.BLOCKCHAIN_SCRIPTS_PATH).resolve()
        self.register_script = scripts_path / "registerStartup.js"
        self.add_employee_script = scripts_path / "addEmployee.js"
    
    def register_startup(
        self,
        startup_name: str,
        sector: str,
        founder_address: str
    ) -> Dict[str, Any]:
        """
        Register a new startup on-chain.
        
        Returns:
            {
                "startup_id": str,
                "transaction_signature": str,
                "blockchain_proof": dict,
                "timestamp": str
            }
        """
        try:
            logger.info(f"Registering startup: {startup_name}")
            
            # Call Node.js script
            # Use absolute path and set working directory to script's parent
            script_path = str(self.register_script.resolve())
            script_dir = str(self.register_script.parent.resolve())
            
            result = subprocess.run(
                [
                    "node",
                    script_path,
                    startup_name,
                    sector,
                    founder_address
                ],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=script_dir
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                logger.error(f"Startup registration failed: {error_msg}")
                raise BlockchainError(f"Failed to register startup: {error_msg}")
            
            # Parse JSON response
            response_data = parse_json_response(result.stdout)
            
            # Normalize keys from camelCase to snake_case
            normalized_response = {
                "startup_id": response_data.get("startupId"),
                "transaction_signature": response_data.get("transactionSignature"),
                "blockchain_proof": response_data.get("blockchainProof"),
                "timestamp": response_data.get("timestamp"),
            }
            
            logger.info(f"Startup registered: {normalized_response.get('startup_id')}")
            
            return normalized_response
            
        except subprocess.TimeoutExpired:
            raise BlockchainError("Startup registration timed out")
        except Exception as e:
            logger.error(f"Error registering startup: {str(e)}")
            raise BlockchainError(f"Startup registration error: {str(e)}")
    
    def add_employee(
        self,
        startup_id: str,
        certificate_id: str,
        employee_address: str
    ) -> Dict[str, Any]:
        """
        Add an employee with verified certificate to a startup.
        Performs on-chain verification of certificate.
        
        Returns:
            {
                "startup_id": str,
                "certificate_id": str,
                "transaction_signature": str,
                "blockchain_proof": dict,
                "timestamp": str
            }
        """
        try:
            logger.info(f"Adding employee {employee_address} to startup {startup_id}")
            
            # Call Node.js script
            # Use absolute path and set working directory to script's parent
            script_path = str(self.add_employee_script.resolve())
            script_dir = str(self.add_employee_script.parent.resolve())
            
            result = subprocess.run(
                [
                    "node",
                    script_path,
                    startup_id,
                    certificate_id,
                    employee_address
                ],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=script_dir
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                logger.error(f"Add employee failed: {error_msg}")
                raise BlockchainError(f"Failed to add employee: {error_msg}")
            
            # Parse JSON response
            response_data = parse_json_response(result.stdout)
            
            # Normalize keys from camelCase to snake_case
            normalized_response = {
                "startup_id": response_data.get("startupId"),
                "certificate_id": response_data.get("certificateId"),
                "transaction_signature": response_data.get("transactionSignature"),
                "blockchain_proof": response_data.get("blockchainProof"),
                "timestamp": response_data.get("timestamp"),
            }
            
            logger.info(f"Employee added successfully")
            
            return normalized_response
            
        except subprocess.TimeoutExpired:
            raise BlockchainError("Add employee operation timed out")
        except Exception as e:
            logger.error(f"Error adding employee: {str(e)}")
            raise BlockchainError(f"Add employee error: {str(e)}")
    
    def get_startup_data(self, startup_id: str) -> Dict[str, Any]:
        """
        Get startup data from blockchain.
        Note: This would require querying the on-chain account.
        For now, returns basic info structure.
        """
        # In a full implementation, you'd query the Solana account
        # For now, return a placeholder structure
        return {
            "startup_id": startup_id,
            "verified": True,
            "on_chain": True
        }

