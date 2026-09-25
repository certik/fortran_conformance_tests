! rule: S16.9.101-002
! covers: IANY-result-shape-removes-dim
program i169m_iany_dim_shape
  implicit none
  integer :: grid(2,3), checks
  checks = 0
  grid = reshape([1, 2, 4, 8, 16, 32], [2, 3])
  call require('IANY DIM shape removes selected extent', &
       all(shape(iany(grid, dim=1)) == [3]) .and. all(shape(iany(grid, dim=2)) == [2]), checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 M IANY DIM SHAPE OK'
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
end program i169m_iany_dim_shape
