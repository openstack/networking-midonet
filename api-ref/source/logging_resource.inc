.. -*- rst -*-
.. needs:method_verification
.. needs:parameter_verification
.. needs:example_verification
.. needs:body_verification

===================
 Logging Resources
===================

Lists, shows information for, creates, updates and deletes logging resources.

List Logging Resources
======================

.. rest_method:: GET /v2.0/logging/logging_resources.json

Lists logging resources.

Normal response codes: 200

Error response codes: unauthorized(401), forbidden(403)

Request
-------

Response
--------

.. rest_parameters:: parameters.yaml

  - id: logging_resource_id-body
  - tenant_id: project_id
  - project_id: project_id
  - name: name
  - description: description
  - enabled: logging_resource_enabled

Response Example
----------------

.. literalinclude:: samples/logging_resource/logging_resources-list-response.json
   :language: javascript

Create Logging Resource
=======================

.. rest_method:: POST /v2.0/logging/logging_resources.json

Creates a logging resource.

Normal response codes: 200

Error response codes: badRequest(400), unauthorized(401), forbidden(403)

Request
-------

.. rest_parameters:: parameters.yaml

  - tenant_id: project_id-request
  - project_id: project_id-request
  - name: name-request
  - description: description-request
  - enabled: logging_resource_enabled-request

Request Example
---------------

.. literalinclude:: samples/logging_resource/logging_resource-create-request.json
   :language: javascript

Response
--------

.. rest_parameters:: parameters.yaml

  - id: logging_resource_id-body
  - tenant_id: project_id
  - project_id: project_id
  - name: name
  - description: description
  - enabled: logging_resource_enabled

Response Example
----------------

.. literalinclude:: samples/logging_resource/logging_resource-create-response.json
   :language: javascript

Show Logging Resource Details
=============================

.. rest_method:: GET /v2.0/logging/logging_resources/{logging_resource_id}.json

Shows details for a logging resource.

Normal response codes: 200

Error response codes: badRequest(400), unauthorized(401), forbidden(403), itemNotFound(404)

Request
-------

.. rest_parameters:: parameters.yaml

  - logging_resource_id: logging_resource_id

Response
--------

.. rest_parameters:: parameters.yaml

  - id: logging_resource_id-body
  - tenant_id: project_id
  - project_id: project_id
  - name: name
  - description: description
  - enabled: logging_resource_enabled

Response Example
----------------

.. literalinclude:: samples/logging_resource/logging_resource-show-response.json
   :language: javascript

Update Logging Resource
=======================

.. rest_method:: PUT /v2.0/logging/logging_resources/{logging_resource_id}.json

Updates a logging resource.

Normal response codes: 200

Error response codes: badRequest(400), unauthorized(401), forbidden(403), itemNotFound(404)

Request
-------

.. rest_parameters:: parameters.yaml

  - logging_resource_id: logging_resource_id
  - name: name-request-put
  - description: description-request-put
  - enabled: logging_resource_enabled-request-put

Request Example
----------------

.. literalinclude:: samples/logging_resource/logging_resource-update-request.json
   :language: javascript

Response
--------

.. rest_parameters:: parameters.yaml

  - id: logging_resource_id-body
  - tenant_id: project_id
  - project_id: project_id
  - name: name
  - description: description
  - enabled: logging_resource_enabled

Response Example
----------------

.. literalinclude:: samples/logging_resource/logging_resource-update-response.json
   :language: javascript

Delete Logging Resource
=======================

.. rest_method:: DELETE /v2.0/logging/logging_resources/{logging_resource_id}.json

Deletes a logging resource.

Normal response codes: 202

Error response codes: badRequest(400), unauthorized(401), forbidden(403), itemNotFound(404)

Request
-------

.. rest_parameters:: parameters.yaml

  - logging_resource_id: logging_resource_id

Response
--------

There is no body content for the response of a successful Delete request.
