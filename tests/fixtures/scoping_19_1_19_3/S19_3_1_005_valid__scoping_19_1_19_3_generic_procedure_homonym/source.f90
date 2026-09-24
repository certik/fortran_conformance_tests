! rule: S19.3.1-005
! covers: generic-name-same-as-procedure
! evidence: effect
! standard: f2023
! oracle-basis: standard
program scoping_generic_procedure_homonym
  implicit none
  interface chooser
    integer function chooser(x)
      integer, intent(in) :: x
    end function chooser
  end interface
  integer :: checks
  checks = 0
  call expect_equal(chooser(5), 47, 'generic external same name')
  call expect_equal(checks, 1, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 GENERIC PROCEDURE HOMONYM OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'SCOPE-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program scoping_generic_procedure_homonym
integer function chooser(x)
  implicit none
  integer, intent(in) :: x
  chooser = 42 + x
end function chooser
