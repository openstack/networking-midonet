Policies
========

This page explains development policies for `networking-midonet` project.

See also:

- `Neutron Policies <https://docs.openstack.org/neutron/latest/policies/index.html>`_

- `OpenStack Developer's Guide <https://docs.openstack.org/infra/manual/developers.html>`_


Review and merge patches
------------------------

- How to find patches to review

  Unlike some of other gerrit-using communities, (e.g. midonet project
  on gerrithub) a submitter of patches usually doesn't add reviewers
  to their patches explicitly.  (Nor recommended to do so)
  We consider it's reviewer's responsibility to find patches to review.
  There are a few tools available to help the process.

  - Gerrit dashboards [#dashboards]_

  - Email notifications from gerrit [#watched_projects]_

  - Gerrit notifications on Freenode IRC channels,
    #openstack-neutron [#neutron_irc]_ and #midonet [#midonet_irc]_

- We require two +2 votes before merging a patch

  When you merge a patch without two +2 votes, please leave a message
  to explain why.
  E.g. "This is a trivial fix for a problem blocking other projects."

  Usually the reviewer who voted the second +2 also make it Workflow +1.
  It makes zuul run the gate jobs for the patch and merge it
  if tests succeeded.  Of course, it's also ok for the reviewer to
  choose not to put Workflow +1.
  E.g. When he thinks more reviews are desirable.
  E.g. When the gate jobs are known to be broken. (In that case,
  running them would just waste the infra resources.)

- Do not ignore the result of non-voting jobs

  When you merge a patch with non-voting jobs failing, please leave
  a message to explain why.  Please make sure that there's a bug filed
  for the symptom.
  E.g. "Test failures are unrelated to this patch.  bug xxxxxx."

- Document "recheck" reasons

  Writing a comment starting with "recheck" [#recheck_trigger]_
  on the gerrit, you can re-trigger test jobs for the patch.
  Please try to examine the failure and explain why a recheck
  was necessary in the comment.  A bug reference is the most appropriate.
  E.g. "recheck bug xxxxxxx"
  E.g. "recheck builds.midonet.org connection timeout"

- Check the rendered htmls when reviewing document changes

  Test jobs ``build-openstack-sphinx-docs`` and
  ``build-openstack-releasenotes`` provide the rendered results for
  the change.

.. [#dashboards] https://docs.openstack.org/networking-midonet/latest/contributor/dashboards.html#gerrit-dashboards
.. [#watched_projects] https://review.openstack.org/#/settings/projects
.. [#neutron_irc] http://eavesdrop.openstack.org/irclogs/%23openstack-neutron/latest.log.html
.. [#midonet_irc] http://eavesdrop.openstack.org/irclogs/%23midonet/latest.log.html
.. [#recheck_trigger] https://github.com/openstack-infra/project-config/blob/89bc1bf84940cdc565da97c77d203e4d826f4b92/zuul.yaml#L7-L8
