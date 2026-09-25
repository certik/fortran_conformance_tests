module procedure_reference_c1534_m
  implicit none
  abstract interface
    integer function int_fn(n)
      integer, intent(in) :: n
    end function
  end interface
  interface gen
    module procedure inc, rinc
  end interface
contains
  integer function inc(n)
    integer, intent(in) :: n
    inc = n + 1
  end function
  real function rinc(x)
    real, intent(in) :: x
    rinc = x + 1.0
  end function
  integer function apply(f, n)
    procedure(int_fn) :: f
    integer, intent(in) :: n
    apply = f(n)
  end function
end module procedure_reference_c1534_m
program procedure_reference_c1534_invalid
  use procedure_reference_c1534_m
  implicit none
  integer :: x
  x = apply(gen, 4)
end program procedure_reference_c1534_invalid
