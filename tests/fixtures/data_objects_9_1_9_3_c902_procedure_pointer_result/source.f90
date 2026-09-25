! rule: C902
! covers: procedure-pointer-result-excluded
! evidence: effect
! standard: f2023
! oracle-basis: standard
module dataobj_c902_procedure_m
  implicit none
  abstract interface
    subroutine sub_i()
    end subroutine
  end interface
contains
  subroutine target_sub()
  end subroutine
  function f() result(p)
    procedure(sub_i), pointer :: p
    p => target_sub
  end function
end module dataobj_c902_procedure_m
program dataobj_c902_procedure_pointer_result
  use dataobj_c902_procedure_m
  implicit none
  f() = 31
end program dataobj_c902_procedure_pointer_result
