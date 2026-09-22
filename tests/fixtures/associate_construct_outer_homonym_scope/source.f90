! rule: S11.1.3.2-002
! covers: associate-name-not-outside-block-source
! Oracle values are derived from Fortran 2023 11.1.3.2 or 11.1.3.3.
program associate_construct_outer_homonym_scope_effect
  implicit none
  integer :: checks
  integer :: item, target
  item=707
  target=101
  checks=0
  ! Outer item sentinel 707 is distinct from inner writes 303 and target initial 101.
  associate (item => target)
    item=303
  end associate
  if (item /= 707) then
    write(*,'(a)') 'ACF:outer_homonym_scope:outer-sentinel-preserved'
    error stop
  end if
  checks=checks+1
  if (target /= 303) then
    write(*,'(a)') 'ACF:outer_homonym_scope:selector-received-inner-write'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'ACF:outer_homonym_scope:check-total'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE OUTER HOMONYM SCOPE OK'
end program associate_construct_outer_homonym_scope_effect
