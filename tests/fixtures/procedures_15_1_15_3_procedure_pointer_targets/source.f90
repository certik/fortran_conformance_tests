! rule: S15.2.2.4-002
! covers: see fixture.json facets
! evidence: effect
! standard: f2023
module procedure_pointer_targets_m
  implicit none
  abstract interface
    integer function int_fun()
    end function
    integer function int_arg_fun(i)
      integer, intent(in) :: i
    end function
  end interface
contains
  integer function module_answer()
    module_answer = 42
  end function
  integer function module_wrong()
    module_wrong = -999
  end function
end module
integer function ext_answer()
  implicit none
  ext_answer = 42
end function
integer function ext_wrong()
  implicit none
  ext_wrong = -999
end function
program procedure_pointer_targets
  use procedure_pointer_targets_m
  implicit none
  intrinsic :: iabs
  interface
    integer function ext_answer()
    end function
    integer function ext_wrong()
    end function
  end interface
  procedure(int_fun), pointer :: p0
  procedure(int_arg_fun), pointer :: p1
  integer :: result
  p0 => ext_answer
  result = p0()
  if (result /= 42) error stop 1
  p0 => internal_answer
  result = p0()
  if (result /= 42) error stop 2
  p1 => iabs
  result = p1(-42)
  if (result /= 42) error stop 3
  p0 => module_answer
  result = p0()
  if (result /= 42) error stop 4
  print '(a)', 'PROCEDURES 15.2.2.4 PROCEDURE POINTER TARGETS OK'
contains
  integer function internal_answer()
    internal_answer = 42
  end function
  integer function internal_wrong()
    internal_wrong = -999
  end function
  integer function wrong_iabs(i)
    integer, intent(in) :: i
    wrong_iabs = -999
  end function
end program
