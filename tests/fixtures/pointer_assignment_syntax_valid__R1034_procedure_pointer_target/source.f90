program pointer_assignment_syntax_procedure
  implicit none
  abstract interface
    integer function op(x)
      integer, intent(in) :: x
    end function op
  end interface
  procedure(op), pointer :: pp
  pp => double_it
  if (pp(21) /= 42) error stop 301
  write(*,'(a)') 'pointer_assignment_syntax_procedure OK'
contains
  integer function double_it(x)
    integer, intent(in) :: x
    double_it = 2*x
  end function double_it
  integer function triple_it(x)
    integer, intent(in) :: x
    triple_it = 3*x
  end function triple_it
end program pointer_assignment_syntax_procedure
