! rule: S16.9.99-002
! covers: IALL-result-type-kind-from-array
! covers: IALL-result-scalar-without-dim-or-rank-one
! covers: IALL-result-shape-removes-dim
program i169l_iall_result_characteristics
  implicit none
  interface type_code
    procedure type_code_integer, type_code_real
  end interface
  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)
  integer :: checks
  integer(kind=ik) :: wide(3)
  integer :: a2(2,3)
  checks = 0
  wide = int([14, 13, 11], kind=ik)
  a2(:,1) = [14, 11]
  a2(:,2) = [13, 7]
  a2(:,3) = [15, 12]
  call require('IALL result kind follows ARRAY', kind(iall(wide)) == ik, checks)
  call require('IALL rank-one DIM or no DIM result is scalar', &
       size(shape(iall(wide))) == 0 .and. size(shape(iall(wide, dim=1))) == 0, checks)
  call require('IALL DIM result shape removes DIM extent', &
       all(shape(iall(a2, dim=1)) == [3]) .and. all(shape(iall(a2, dim=2)) == [2]), checks)
  if (checks /= 3) error stop
  write(*,'(a)') 'INTRINSICS 16.9 L IALL RESULT CHARACTERISTICS OK'
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
end program i169l_iall_result_characteristics
