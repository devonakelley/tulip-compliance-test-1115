"""
Catalogs API - Forms and Work Instructions
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
import logging
from database.mongodb_manager import get_mongodb
from core.auth_utils import get_current_user_from_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/catalogs", tags=["catalogs"])


@router.get("/forms")
async def get_forms_catalog(
    current_user: dict = Depends(get_current_user_from_token)
):
    """
    Get all forms in the catalog
    
    Returns:
        List of forms with id, name, parent QSP, and referenced sections
    """
    try:
        db = await get_mongodb()
        tenant_id = current_user.get('tenant_id')
        
        forms = await db.forms_catalog.find(
            {'tenant_id': tenant_id}
        ).sort('form_id', 1).to_list(length=1000)
        
        # Convert ObjectId to string and format response
        result = []
        for form in forms:
            result.append({
                'form_id': form.get('form_id'),
                'form_name': form.get('form_name'),
                'parent_qsp': form.get('parent_qsp'),
                'description': form.get('description'),
                'referenced_in_sections': form.get('referenced_in_sections', []),
                'created_at': form.get('created_at'),
                'updated_at': form.get('updated_at')
            })
        
        return {
            'success': True,
            'total': len(result),
            'forms': result
        }
        
    except Exception as e:
        logger.error(f"Failed to get forms catalog: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/work-instructions")
async def get_wi_catalog(
    current_user: dict = Depends(get_current_user_from_token)
):
    """
    Get all work instructions in the catalog
    
    Returns:
        List of WIs with id, name, parent QSP, and referenced sections
    """
    try:
        db = await get_mongodb()
        tenant_id = current_user.get('tenant_id')
        
        wis = await db.wi_catalog.find(
            {'tenant_id': tenant_id}
        ).sort('wi_id', 1).to_list(length=1000)
        
        # Convert ObjectId to string and format response
        result = []
        for wi in wis:
            result.append({
                'wi_id': wi.get('wi_id'),
                'wi_name': wi.get('wi_name'),
                'parent_qsp': wi.get('parent_qsp'),
                'description': wi.get('description'),
                'referenced_in_sections': wi.get('referenced_in_sections', []),
                'created_at': wi.get('created_at'),
                'updated_at': wi.get('updated_at')
            })
        
        return {
            'success': True,
            'total': len(result),
            'work_instructions': result
        }
        
    except Exception as e:
        logger.error(f"Failed to get WI catalog: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_catalogs_summary(
    current_user: dict = Depends(get_current_user_from_token)
):
    """
    Get summary of all catalogs
    
    Returns:
        Summary with counts by parent QSP
    """
    try:
        db = await get_mongodb()
        tenant_id = current_user.get('tenant_id')
        
        # Get all forms
        forms = await db.forms_catalog.find({'tenant_id': tenant_id}).to_list(length=1000)
        
        # Get all WIs
        wis = await db.wi_catalog.find({'tenant_id': tenant_id}).to_list(length=1000)
        
        # Group by parent QSP
        by_qsp = {}
        
        for form in forms:
            parent = form.get('parent_qsp', 'Unknown')
            if parent not in by_qsp:
                by_qsp[parent] = {'forms': [], 'wis': []}
            by_qsp[parent]['forms'].append({
                'id': form.get('form_id'),
                'name': form.get('form_name')
            })
        
        for wi in wis:
            parent = wi.get('parent_qsp', 'Unknown')
            if parent not in by_qsp:
                by_qsp[parent] = {'forms': [], 'wis': []}
            by_qsp[parent]['wis'].append({
                'id': wi.get('wi_id'),
                'name': wi.get('wi_name')
            })
        
        return {
            'success': True,
            'total_forms': len(forms),
            'total_wis': len(wis),
            'by_qsp': by_qsp
        }
        
    except Exception as e:
        logger.error(f"Failed to get catalogs summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
