! rule: S16.9.99-001
! covers: IALL-ARRAY-integer-array
! covers: IALL-DIM-integer-scalar-valid-range
! covers: IALL-MASK-logical-conformable
program i169l_iall_argument_controls
  implicit none
  interface type_code
    procedure type_code_integer, type_code_real
  end interface
  integer :: checks
  integer :: a2(2,3), k
  integer :: r1(3), r2(2), rm(3)
  logical :: mask2(2,3)
  checks = 0
  a2(:,1) = [14, 11]
  a2(:,2) = [13, 7]
  a2(:,3) = [15, 12]
  mask2(:,1) = [.true., .true.]
  mask2(:,2) = [.true., .false.]
  mask2(:,3) = [.false., .false.]
  call require('IALL accepts integer ARRAY', &
       btest(iall([14, 13, 11]), 3) .and. .not. btest(iall([14, 13, 11]), 2), checks)
  call require('IALL accepts valid scalar DIM', &
       all(shape(iall(a2, dim=1)) == [3]) .and. all(shape(iall(a2, dim=2)) == [2]), checks)
  call require('IALL accepts conformable logical MASK', &
       btest(iall(a2, mask=mask2), 3) .and. .not. btest(iall(a2, mask=mask2), 1), checks)
  if (checks /= 3) error stop
  write(*,'(a)') 'INTRINSICS 16.9 L IALL ARGUMENT CONTROLS OK'
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
end program i169l_iall_argument_controls
