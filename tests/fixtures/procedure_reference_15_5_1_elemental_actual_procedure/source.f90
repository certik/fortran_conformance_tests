module procedure_reference_c1533_m
  implicit none
  abstract interface
    integer function int_fn(n)
      integer, intent(in) :: n
    end function
  end interface
contains
  elemental integer function elem(n)
    integer, intent(in) :: n
    elem = n + 1
  end function
  integer function apply(f, n)
    procedure(int_fn) :: f
    integer, intent(in) :: n
    apply = f(n)
  end function
end module procedure_reference_c1533_m
program procedure_reference_c1533_invalid
  use procedure_reference_c1533_m
  implicit none
  integer :: x
  x = apply(elem, 4)
end program procedure_reference_c1533_invalid
