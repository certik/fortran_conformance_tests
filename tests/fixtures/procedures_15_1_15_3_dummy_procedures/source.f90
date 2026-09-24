! rule: S15.2.2.3-001
! covers: see fixture.json facets
! evidence: effect
! standard: f2023
module dummy_procedures_m
  implicit none
  abstract interface
    integer function int_fun()
    end function
    integer function int_arg_fun(i)
      integer, intent(in) :: i
    end function
    subroutine sub_proc(x)
      integer, intent(inout) :: x
    end subroutine
  end interface
contains
  integer function answer()
    answer = 42
  end function
  subroutine apply_sub(proc, x)
    procedure(sub_proc) :: proc
    integer, intent(inout) :: x
    call proc(x)
  end subroutine
  subroutine apply_fun(proc, y)
    procedure(int_arg_fun) :: proc
    integer, intent(out) :: y
    y = proc(41)
  end subroutine
  subroutine call_pointer(proc, y)
    procedure(int_fun), pointer :: proc
    integer, intent(out) :: y
    y = proc()
  end subroutine
end module
integer function plus_one(i)
  implicit none
  integer, intent(in) :: i
  plus_one = i + 1
end function
subroutine bump(x)
  implicit none
  integer, intent(inout) :: x
  x = x + 1
end subroutine
program dummy_procedures
  use dummy_procedures_m
  implicit none
  interface
    integer function plus_one(i)
      integer, intent(in) :: i
    end function
    subroutine bump(x)
      integer, intent(inout) :: x
    end subroutine
  end interface
  procedure(int_fun), pointer :: p
  integer :: x, y
  x = 41
  call apply_sub(bump, x)
  if (x /= 42) error stop 1
  y = -777
  call apply_fun(plus_one, y)
  if (y /= 42) error stop 2
  p => answer
  y = -3
  call call_pointer(p, y)
  if (y /= 42) error stop 3
  print '(a)', 'PROCEDURES 15.2.2.3 DUMMY PROCEDURES OK'
end program
