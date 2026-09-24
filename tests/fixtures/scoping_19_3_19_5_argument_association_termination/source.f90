! rule: S19.5.1.2-003
! covers: argument-association-terminates-on-return
! covers: subsequent-invocation-new-effective-argument
program scoping_19_3_19_5_argument_association_termination
  implicit none
  integer :: checks
  integer :: a, b, first_seen, second_seen
  checks = 0
  a = 1
  b = 2
  first_seen = -1
  second_seen = -2
  call set_dummy(a, 42, first_seen)
  call set_dummy(b, 77, second_seen)
  if (a /= 42) then
    write(*,'(a)') 'SCOPE:argument_association_termination:first-actual'
    error stop
  end if
  checks = checks + 1
  if (b /= 77) then
    write(*,'(a)') 'SCOPE:argument_association_termination:second-actual'
    error stop
  end if
  checks = checks + 1
  if (first_seen /= 42) then
    write(*,'(a)') 'SCOPE:argument_association_termination:first-seen'
    error stop
  end if
  checks = checks + 1
  if (second_seen /= 77) then
    write(*,'(a)') 'SCOPE:argument_association_termination:second-seen'
    error stop
  end if
  checks = checks + 1
  if (checks /= 4) then
    write(*,'(a)') 'SCOPE:argument_association_termination:check-count'
    error stop
  end if
  write(*,'(a)') 'SCOPING 19.3-19.5 ARGUMENT ASSOCIATION TERMINATION OK'
contains
  subroutine set_dummy(d, value, seen)
    integer, intent(inout) :: d
    integer, intent(in) :: value
    integer, intent(out) :: seen
    d = value
    seen = d
  end subroutine
end program scoping_19_3_19_5_argument_association_termination
