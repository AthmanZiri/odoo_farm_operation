================================================================
Recycle Bin
================================================================

The **Recycle Bin** module for Odoo ensures that deleted records are not permanently lost by moving them to a temporary storage area. It allows users to recover deleted data when needed and provides control over record retention periods, restoration, and permanent deletion. With detailed logging and role-based access control, this module enhances data security and operational transparency.

**Table of Contents**
======================
.. contents::
   :local:

**Key Features**
================================================================

- **Recycle Bin for All Records**: Records are not permanently removed when deleted. Instead, they are moved to a recycle bin, providing a way to recover them if needed
- **Customizable Retention Periods**: Businesses can define how long deleted records remain in the recycle bin before being automatically removed permanently.
- **Role-Based Access Control**: Role-based permissions are provided to ensure that only authorized personnel can access and perform actions like restore or delete on the recycle bin.
- **Recycle Bin Logs**: Detailed history of actions such as deletions, restorations, and permanent deletions. This ensures transparency and accountability for all operations performed within the recycle bin.
- **Restore Deleted Records**: Recover deleted records directly from the recycle bin, restoring them with all associated data exactly as it was before deletion.
- **Exclude Models from Recycle**: Provides the ability to exclude specific models from the recycle bin functionality, giving flexibility in deciding which records are managed by this feature.

**Summary**
================================================================

The **Recycle Bin** module for Odoo ensures that deleted records are temporarily stored in a recycle bin, allowing users to restore them if needed. The module also provides features like role-based access control, audit logging, customizable retention periods, and easy-to-use management tools for handling deleted records.

**Installation**
================================================================

1. Clone or download the module from the repository.
2. Place the module in your Odoo addons directory.
3. Restart the Odoo server to update the app list.
4. Install the **Recycle Bin** module from the Odoo Apps menu.

**How to Use This Module**
================================================================

1. **Manage Deleted Records**: Navigate to the Recycle Bin menu to view and manage deleted records, categorized by record type.
2. **Restore Deleted Records**: Authorized users can restore deleted records directly from the recycle bin with a single click.
3. **Audit and Logs**: Monitor and export detailed logs of actions performed on deleted records for accountability and compliance.
4. **Set Retention Policies**: Define how long deleted records should remain in the recycle bin before automatic removal.

**Change Logs**
================================================================

[1.0.0]  
---------------------
* ``Added`` [10-12-2025] Initial release of the Recycle Bin module.

**Support**
================================================================

`Zehntech Technologies <https://www.zehntech.com/erp-crm/odoo-services/>`_
