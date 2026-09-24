! rule: S16.9.72-002
! covers: DIM-result-same-type-kind-as-X
program i169h_dim_result_characteristics
  implicit none
  integer :: checks
  checks = 0
  call require('DIM result has X kind', kind(dim(7, 2)) == kind(0) .and. kind(dim(7.0d0, 2.0d0)) == kind(0.0d0), checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DIM RESULT CHARACTERISTICS OK'
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
end program i169h_dim_result_characteristics
