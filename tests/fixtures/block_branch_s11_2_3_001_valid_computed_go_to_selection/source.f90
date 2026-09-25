program computed_go_to_selection
implicit none
integer :: observed(5)
observed=-99
call choose(1, observed(1))
call choose(2, observed(2))
call choose(3, observed(3))
call choose(0, observed(4))
call choose(4, observed(5))
if (any(observed /= [11,22,33,44,44])) error stop 1
write(*,'(a)') 'COMPUTED GO TO SELECTION OK'
contains
subroutine choose(selector, out)
  implicit none
  integer, intent(in) :: selector
  integer, intent(out) :: out
  out=-7
  go to (100,200,300), selector
  out=44
  return
100 out=11
  return
200 out=22
  return
300 out=33
end subroutine choose
end program computed_go_to_selection
