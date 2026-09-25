module procedure_reference_15_5_1_actual_proc_m
  implicit none
  abstract interface
    integer function int_fn(n)
      integer, intent(in) :: n
    end function
  end interface
  type holder
    procedure(int_fn), pointer, nopass :: op => null()
  end type
contains
  integer function inc(n)
    integer, intent(in) :: n
    inc = n + 1
  end function
  integer function dec(n)
    integer, intent(in) :: n
    dec = n - 1
  end function
  integer function apply(f, n)
    procedure(int_fn) :: f
    integer, intent(in) :: n
    apply = f(n)
  end function
end module procedure_reference_15_5_1_actual_proc_m

program procedure_reference_15_5_1_actual_proc
  use procedure_reference_15_5_1_actual_proc_m
  implicit none
  type(holder) :: h
  integer :: by_name, by_component, checks
  checks = 0
  by_name = -9
  by_name = apply(inc, 4)
  if (by_name /= 5) error stop 401
  checks = checks + 1
  h%op => inc
  by_component = -8
  by_component = apply(h%op, 5)
  if (by_component /= 6) error stop 402
  checks = checks + 1
  if (checks /= 2) error stop 499
  print '(a)', 'PROCEDURE REFERENCE PROCEDURE ACTUALS OK'
end program procedure_reference_15_5_1_actual_proc
