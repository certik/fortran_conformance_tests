! rule: S15.2.2.2-001
! covers: see fixture.json facets
! evidence: effect
! standard: f2023
integer function ext_answer()
  implicit none
  ext_answer = 42
end function
integer function wrong_answer()
  implicit none
  wrong_answer = -999
end function
program external_subprogram
  implicit none
  interface
    integer function ext_answer()
    end function
    integer function wrong_answer()
    end function
  end interface
  integer :: result
  result = -777
  result = ext_answer()
  if (result /= 42) error stop 1
  print '(a)', 'PROCEDURES 15.2.2.2 EXTERNAL SUBPROGRAM OK'
end program
