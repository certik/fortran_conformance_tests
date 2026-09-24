! rule: S19.5.1.2-002
! covers: dummy-name-may-differ
! covers: dummy-name-accesses-effective-argument
program scoping_19_3_19_5_argument_association_dummy_name
  implicit none
  integer :: checks
  integer :: actual_value, formal
  checks = 0
  actual_value = 1
  formal = -777
  call rename_probe(actual_value)
  if (actual_value /= 42) then
    write(*,'(a)') 'SCOPE:argument_association_dummy_name:dummy-accesses-effective'
    error stop
  end if
  checks = checks + 1
  if (formal /= -777) then
    write(*,'(a)') 'SCOPE:argument_association_dummy_name:host-homonym'
    error stop
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'SCOPE:argument_association_dummy_name:check-count'
    error stop
  end if
  write(*,'(a)') 'SCOPING 19.3-19.5 ARGUMENT ASSOCIATION DUMMY NAME OK'
contains
  subroutine rename_probe(formal)
    integer, intent(inout) :: formal
    formal = 42
  end subroutine
end program scoping_19_3_19_5_argument_association_dummy_name
