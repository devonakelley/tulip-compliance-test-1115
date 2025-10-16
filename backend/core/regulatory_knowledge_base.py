"""
Regulatory Knowledge Base
Pre-populated with key clauses from all regulatory frameworks
"""
from models.regulatory import RegulatoryClause, RegulatoryFramework

# Key regulatory clauses for compliance tracking
REGULATORY_CLAUSES = [
    # FDA 21 CFR Part 820 - Quality System Regulation
    RegulatoryClause(
        framework=RegulatoryFramework.FDA_21CFR820,
        clause_id="820.20",
        title="Management Responsibility",
        requirement_text="Establish and maintain quality policy and objectives",
        category="Management",
        criticality="high",
        keywords=["management", "quality policy", "responsibility"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.FDA_21CFR820,
        clause_id="820.30",
        title="Design Controls",
        requirement_text="Establish and maintain procedures to control design of devices",
        category="Design",
        criticality="high",
        keywords=["design", "development", "validation", "verification"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.FDA_21CFR820,
        clause_id="820.40",
        title="Document Controls",
        requirement_text="Establish and maintain procedures to control all documents",
        category="Documentation",
        criticality="high",
        keywords=["document control", "procedures", "records"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.FDA_21CFR820,
        clause_id="820.50",
        title="Purchasing Controls",
        requirement_text="Establish and maintain procedures for purchasing",
        category="Purchasing",
        criticality="medium",
        keywords=["purchasing", "suppliers", "evaluation"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.FDA_21CFR820,
        clause_id="820.70",
        title="Production and Process Controls",
        requirement_text="Develop, conduct, control, and monitor production processes",
        category="Production",
        criticality="high",
        keywords=["production", "process control", "manufacturing"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.FDA_21CFR820,
        clause_id="820.75",
        title="Process Validation",
        requirement_text="Validate processes with high degree of assurance",
        category="Validation",
        criticality="high",
        keywords=["validation", "process validation", "verification"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.FDA_21CFR820,
        clause_id="820.80",
        title="Receiving, In-Process, and Finished Device Acceptance",
        requirement_text="Establish and maintain procedures for acceptance activities",
        category="Acceptance",
        criticality="high",
        keywords=["acceptance", "inspection", "testing"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.FDA_21CFR820,
        clause_id="820.90",
        title="Nonconforming Product",
        requirement_text="Establish and maintain procedures to control nonconforming product",
        category="Quality Control",
        criticality="high",
        keywords=["nonconforming", "deviation", "quality"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.FDA_21CFR820,
        clause_id="820.100",
        title="Corrective and Preventive Action",
        requirement_text="Establish and maintain procedures for CAPA",
        category="CAPA",
        criticality="high",
        keywords=["CAPA", "corrective action", "preventive action"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.FDA_21CFR820,
        clause_id="820.170",
        title="Installation",
        requirement_text="Establish and maintain adequate installation procedures",
        category="Installation",
        criticality="medium",
        keywords=["installation", "procedures"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.FDA_21CFR820,
        clause_id="820.198",
        title="Complaint Files",
        requirement_text="Maintain complaint files and procedures",
        category="Post-Market",
        criticality="high",
        keywords=["complaints", "feedback", "post-market"]
    ),
    
    # ISO 13485:2016
    RegulatoryClause(
        framework=RegulatoryFramework.ISO_13485,
        clause_id="4.1",
        title="Quality Management System - General Requirements",
        requirement_text="Establish, document, implement and maintain a QMS",
        category="QMS",
        criticality="high",
        keywords=["QMS", "quality management", "documentation"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.ISO_13485,
        clause_id="4.2",
        title="Documentation Requirements",
        requirement_text="QMS documentation shall include quality manual, procedures, records",
        category="Documentation",
        criticality="high",
        keywords=["documentation", "quality manual", "procedures"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.ISO_13485,
        clause_id="5.5",
        title="Management Representative",
        requirement_text="Appoint management representative with defined responsibility",
        category="Management",
        criticality="high",
        keywords=["management representative", "responsibility"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.ISO_13485,
        clause_id="6.2",
        title="Human Resources",
        requirement_text="Ensure competence of personnel affecting product quality",
        category="HR",
        criticality="high",
        keywords=["training", "competence", "personnel"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.ISO_13485,
        clause_id="7.1",
        title="Planning of Product Realization",
        requirement_text="Plan and develop processes for product realization",
        category="Planning",
        criticality="high",
        keywords=["planning", "product realization", "risk management"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.ISO_13485,
        clause_id="7.2",
        title="Customer-Related Processes",
        requirement_text="Determine and review product requirements",
        category="Customer",
        criticality="medium",
        keywords=["customer", "requirements", "review"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.ISO_13485,
        clause_id="7.3",
        title="Design and Development",
        requirement_text="Control design and development of medical devices",
        category="Design",
        criticality="high",
        keywords=["design", "development", "validation", "verification"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.ISO_13485,
        clause_id="7.4",
        title="Purchasing",
        requirement_text="Ensure purchased product meets requirements",
        category="Purchasing",
        criticality="medium",
        keywords=["purchasing", "suppliers", "verification"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.ISO_13485,
        clause_id="7.5",
        title="Production and Service Provision",
        requirement_text="Control production and service provision",
        category="Production",
        criticality="high",
        keywords=["production", "manufacturing", "service"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.ISO_13485,
        clause_id="7.6",
        title="Control of Monitoring and Measuring Equipment",
        requirement_text="Determine and control monitoring and measuring equipment",
        category="Equipment",
        criticality="medium",
        keywords=["calibration", "monitoring", "measuring"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.ISO_13485,
        clause_id="8.2",
        title="Monitoring and Measurement",
        requirement_text="Monitor and measure processes and product",
        category="Monitoring",
        criticality="high",
        keywords=["monitoring", "measurement", "audit"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.ISO_13485,
        clause_id="8.3",
        title="Control of Nonconforming Product",
        requirement_text="Ensure nonconforming product is identified and controlled",
        category="Quality Control",
        criticality="high",
        keywords=["nonconforming", "deviation", "control"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.ISO_13485,
        clause_id="8.5",
        title="Improvement - CAPA",
        requirement_text="Take action to eliminate causes of nonconformities",
        category="CAPA",
        criticality="high",
        keywords=["CAPA", "improvement", "corrective action"]
    ),
    
    # MDR 2017/745
    RegulatoryClause(
        framework=RegulatoryFramework.MDR_2017_745,
        clause_id="Article 10",
        title="General Obligations of Manufacturers",
        requirement_text="Manufacturers shall ensure devices are designed and manufactured per GSPR",
        category="General",
        criticality="high",
        keywords=["manufacturer", "obligations", "GSPR"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.MDR_2017_745,
        clause_id="Article 15",
        title="Person Responsible for Regulatory Compliance",
        requirement_text="Manufacturers shall have available person responsible for regulatory compliance",
        category="Management",
        criticality="high",
        keywords=["regulatory compliance", "PRRC", "responsibility"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.MDR_2017_745,
        clause_id="Article 61",
        title="Clinical Evaluation",
        requirement_text="Clinical evaluation shall be performed for all devices",
        category="Clinical",
        criticality="high",
        keywords=["clinical evaluation", "CER", "clinical data"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.MDR_2017_745,
        clause_id="Article 83",
        title="Post-Market Surveillance System",
        requirement_text="Manufacturers shall plan and establish PMS system",
        category="Post-Market",
        criticality="high",
        keywords=["PMS", "post-market surveillance", "vigilance"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.MDR_2017_745,
        clause_id="Article 86",
        title="Periodic Safety Update Report",
        requirement_text="Manufacturers shall prepare PSUR for devices",
        category="Post-Market",
        criticality="high",
        keywords=["PSUR", "safety", "reporting"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.MDR_2017_745,
        clause_id="Annex I",
        title="General Safety and Performance Requirements",
        requirement_text="Devices shall meet general safety and performance requirements",
        category="GSPR",
        criticality="high",
        keywords=["GSPR", "safety", "performance", "requirements"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.MDR_2017_745,
        clause_id="Annex II",
        title="Technical Documentation",
        requirement_text="Technical documentation shall demonstrate conformity",
        category="Documentation",
        criticality="high",
        keywords=["technical documentation", "TF", "conformity"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.MDR_2017_745,
        clause_id="Annex III",
        title="Technical Documentation on Post-Market Surveillance",
        requirement_text="Documentation for PMS including PMCF plan",
        category="Post-Market",
        criticality="high",
        keywords=["PMCF", "PMS plan", "post-market"]
    ),
    
    # ISO 14971:2019 - Risk Management
    RegulatoryClause(
        framework=RegulatoryFramework.ISO_14971,
        clause_id="4",
        title="General Requirements for Risk Management",
        requirement_text="Establish risk management process for medical devices",
        category="Risk Management",
        criticality="high",
        keywords=["risk management", "process", "system"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.ISO_14971,
        clause_id="5",
        title="Risk Analysis",
        requirement_text="Identify hazards and estimate risks",
        category="Risk Management",
        criticality="high",
        keywords=["risk analysis", "hazards", "estimation"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.ISO_14971,
        clause_id="6",
        title="Risk Evaluation",
        requirement_text="Evaluate whether risk reduction is required",
        category="Risk Management",
        criticality="high",
        keywords=["risk evaluation", "acceptability", "criteria"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.ISO_14971,
        clause_id="7",
        title="Risk Control",
        requirement_text="Implement risk control measures",
        category="Risk Management",
        criticality="high",
        keywords=["risk control", "mitigation", "measures"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.ISO_14971,
        clause_id="8",
        title="Evaluation of Overall Residual Risk",
        requirement_text="Evaluate overall residual risk acceptability",
        category="Risk Management",
        criticality="high",
        keywords=["residual risk", "overall risk", "evaluation"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.ISO_14971,
        clause_id="9",
        title="Risk Management Review",
        requirement_text="Review risk management activities before release",
        category="Risk Management",
        criticality="high",
        keywords=["review", "risk management file", "documentation"]
    ),
    RegulatoryClause(
        framework=RegulatoryFramework.ISO_14971,
        clause_id="10",
        title="Production and Post-Production Activities",
        requirement_text="Collect and review information in production and post-production",
        category="Risk Management",
        criticality="high",
        keywords=["production", "post-production", "monitoring"]
    ),
    
    # ISO 10993 - Biocompatibility
    RegulatoryClause(
        framework=RegulatoryFramework.ISO_10993,
        clause_id="10993-1",
        title="Evaluation and Testing within Risk Management",
        requirement_text="Biological evaluation as part of risk management",
        category="Biocompatibility",
        criticality="high",
        keywords=["biocompatibility", "biological evaluation", "testing"]
    ),
    
    # ISO 11135 - Sterilization
    RegulatoryClause(
        framework=RegulatoryFramework.ISO_11135,
        clause_id="General",
        title="Ethylene Oxide Sterilization",
        requirement_text="Requirements for development, validation and routine control of EtO sterilization",
        category="Sterilization",
        criticality="high",
        keywords=["sterilization", "EtO", "validation"]
    ),
    
    # ISO 11607 - Packaging
    RegulatoryClause(
        framework=RegulatoryFramework.ISO_11607,
        clause_id="General",
        title="Packaging for Terminally Sterilized Medical Devices",
        requirement_text="Requirements for materials, sterile barrier systems, and packaging systems",
        category="Packaging",
        criticality="high",
        keywords=["packaging", "sterile barrier", "validation"]
    ),
    
    # 21 CFR Part 11 - Electronic Records
    RegulatoryClause(
        framework=RegulatoryFramework.CFR_PART_11,
        clause_id="11.10",
        title="Controls for Closed Systems",
        requirement_text="Validation, audit trails, authority checks, device checks",
        category="Electronic Records",
        criticality="high",
        keywords=["electronic records", "validation", "audit trail", "e-signature"]
    ),
    
    # MDSAP
    RegulatoryClause(
        framework=RegulatoryFramework.MDSAP,
        clause_id="General",
        title="Medical Device Single Audit Program",
        requirement_text="Single regulatory audit program for medical devices",
        category="Audits",
        criticality="medium",
        keywords=["MDSAP", "audit", "multi-country", "regulatory"]
    ),
]

def get_all_clauses():
    """Get all regulatory clauses"""
    return REGULATORY_CLAUSES

def get_clauses_by_framework(framework: RegulatoryFramework):
    """Get clauses for specific framework"""
    return [c for c in REGULATORY_CLAUSES if c.framework == framework]

def get_clause_by_id(framework: RegulatoryFramework, clause_id: str):
    """Get specific clause"""
    for clause in REGULATORY_CLAUSES:
        if clause.framework == framework and clause.clause_id == clause_id:
            return clause
    return None
