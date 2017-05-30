Policies
========

This page explains development policies for `networking-midonet` project.

See also:

    - `Neutron Policies <https://docs.openstack.org/developer/neutron/policies/index.html>`_

    - `OpenStack Developer's Guide <https://docs.openstack.org/infra/manual/developers.html>`_


Review and merge patches
------------------------

- We require two +2 votes before merging a patch.

  When you merge a patch without two +2 votes, please leave a message
  to explain why.
  E.g. "This is a trivial fix for a problem blocking other projects."

  Usually the reviewer who voted the second +2 also make it Workflow +1.
  It makes the jenkins run the gate jobs for the patch and merge it
  if tests succeeded.  Of course, it's also ok for the reviewer to
  choose not to put Workflow +1.
  E.g. When he thinks more reviews are desirable.
  E.g. When the gate jobs are known to be broken. (In that case,
  running them would just waste the infra resources.)

- Do not ignore the result of non-voting jobs.

  When you merge a patch with non-voting jobs failinig, please leave
  a message to explain why.  Please make sure that there's a bug filed
  for the symptom.
  E.g. "Jenkins failures are unrelated to this patch.  bug xxxxxx."

- Document "recheck" reasons.

  Writing a comment starting with "recheck" [#recheck_trigger]_
  on the gerrit, you can re-trigger jenkins jobs for the patch.
  Please try to examine the failure and explain why a recheck
  was necessary in the comment.  A bug reference is the most appropriate.
  E.g. "recheck bug xxxxxxx"
  E.g. "recheck builds.midonet.org connection timeout"

.. [#recheck_trigger] https://github.com/openstack-infra/project-config/blob/89bc1bf84940cdc565da97c77d203e4d826f4b92/zuul.yaml#L7-L8
