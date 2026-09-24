! rule: S16.9.96-002
! covers: HUGE-result-scalar
! covers: HUGE-result-same-type-and-kind-as-X
program i169l_huge_result_characteristics
  implicit none
  interface type_code
    procedure type_code_integer, type_code_real
  end interface
  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)
  integer :: checks
  integer(kind=ik) :: wide(2)
  real(kind=8) :: rd
  checks = 0
  wide = [1_ik, 2_ik]
  rd = 1.0_8
  call require('HUGE result is scalar even for arrays', &
       size(shape(huge(wide))) == 0 .and. size(shape(huge([rd, rd]))) == 0, checks)
  call require('HUGE result has X type and kind', &
       type_code(huge(1)) == 1 .and. type_code(huge(1.0)) == 2 .and. &
       kind(huge(wide)) == ik .and. kind(huge(rd)) == kind(rd), checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 L HUGE RESULT CHARACTERISTICS OK'
contains
  subroutine require(label, condition, checks)
    character(len=*), intent(in) :: label
    logical, intent(in) :: condition
    integer, intent(inout) :: checks
    if (.not. condition) then
      write(*,'(a)') label
      error stop
    end if
    checks = checks + 1
  end subroutine require
  integer function type_code_integer(x)
    integer, intent(in) :: x
    type_code_integer = 1
  end function type_code_integer
  integer function type_code_real(x)
    real, intent(in) :: x
    type_code_real = 2
  end function type_code_real
end program i169l_huge_result_characteristics
