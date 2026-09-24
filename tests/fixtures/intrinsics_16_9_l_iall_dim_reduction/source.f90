! rule: S16.9.99-005
! covers: IALL-dim-rank-one-equals-whole-array
! covers: IALL-dim-section-wise-reduction
! covers: IALL-dim-mask-section-wise-reduction
program i169l_iall_dim_reduction
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
  call require('IALL rank-one DIM equals whole-array form', &
       all([(btest(iall([14,13,11], dim=1), k) .eqv. &
              btest(iall([14,13,11]), k), k = 0, 4)]), checks)
  r1 = iall(a2, dim=1)
  r2 = iall(a2, dim=2)
  call require('IALL DIM applies to each rank-one section', &
       btest(r1(1), 1) .and. .not. btest(r1(2), 1) .and. &
       btest(r2(1), 2) .and. .not. btest(r2(2), 0), checks)
  rm = iall(a2, dim=1, mask=mask2)
  call require('IALL DIM with MASK applies section masks', &
       btest(rm(1), 1) .and. btest(rm(2), 0) .and. &
       btest(rm(3), bit_size(0)-1), checks)
  if (checks /= 3) error stop
  write(*,'(a)') 'INTRINSICS 16.9 L IALL DIM REDUCTION OK'
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
end program i169l_iall_dim_reduction
