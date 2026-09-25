module procedure_reference_c1533_m
  implicit none
  abstract interface
    integer function int_fn(n)
      integer, intent(in) :: n
    end function
  end interface
contains
  integer function elem(n)
    integer, intent(in) :: n
    elem = n + 1
  end function
  integer function apply(f, n)
    procedure(int_fn) :: f
    integer, intent(in) :: n
    apply = f(n)
  end function
end module procedure_reference_c1533_m
program procedure_reference_c1533_control
  use procedure_reference_c1533_m
  implicit none
  integer :: x
  x = -1
  x = apply(elem, 4)
  if (x /= 5) error stop 1
  print '(a)', 'PROCEDURE REFERENCE C1533 CONTROL OK'
end program procedure_reference_c1533_control
