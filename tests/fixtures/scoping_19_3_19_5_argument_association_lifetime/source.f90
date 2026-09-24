! rule: S19.5.1.2-001
! covers: procedure-reference-establishes-argument-association
! covers: present-dummy-associated-with-effective-argument
program scoping_19_3_19_5_argument_association_lifetime
  implicit none
  integer :: checks
  integer :: first_actual, second_actual, first_seen, second_seen
  checks = 0
  first_actual = 1
  second_actual = -7
  first_seen = -1
  second_seen = -2
  call pair_probe(first_actual, second_actual, first_seen, second_seen)
  if (first_actual /= 42) then
    write(*,'(a)') 'SCOPE:argument_association_lifetime:first-present-dummy'
    error stop
  end if
  checks = checks + 1
  if (second_actual /= 77) then
    write(*,'(a)') 'SCOPE:argument_association_lifetime:second-present-dummy'
    error stop
  end if
  checks = checks + 1
  if (first_seen /= 42) then
    write(*,'(a)') 'SCOPE:argument_association_lifetime:first-seen'
    error stop
  end if
  checks = checks + 1
  if (second_seen /= 77) then
    write(*,'(a)') 'SCOPE:argument_association_lifetime:second-seen'
    error stop
  end if
  checks = checks + 1
  if (checks /= 4) then
    write(*,'(a)') 'SCOPE:argument_association_lifetime:check-count'
    error stop
  end if
  write(*,'(a)') 'SCOPING 19.3-19.5 ARGUMENT ASSOCIATION LIFETIME OK'
contains
  subroutine pair_probe(first_dummy, second_dummy, first_seen, second_seen)
    integer, intent(inout) :: first_dummy, second_dummy
    integer, intent(out) :: first_seen, second_seen
    first_dummy = 42
    second_dummy = 77
    first_seen = first_dummy
    second_seen = second_dummy
  end subroutine
end program scoping_19_3_19_5_argument_association_lifetime
