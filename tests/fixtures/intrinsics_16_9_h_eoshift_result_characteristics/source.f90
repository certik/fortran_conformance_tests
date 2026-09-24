! rule: S16.9.77-006
! covers: EOSHIFT-result-type-params-shape-of-array
program i169h_eoshift_result_characteristics
  implicit none
  integer :: checks
  character(len=3) :: a(2,2)
  checks = 0
  a = reshape([character(len=3) :: 'abc', 'def', 'ghi', 'jkl'], [2, 2])
  call require('EOSHIFT result type parameters and shape follow ARRAY', &
       len(eoshift(a, 1, 'xyz', dim=2)) == 3 .and. &
       all(shape(eoshift(a, 1, 'xyz', dim=2)) == [2, 2]), checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H EOSHIFT RESULT CHARACTERISTICS OK'
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
end program i169h_eoshift_result_characteristics
