! rule: S16.9.101-005
! covers: IANY-dim-rank-one-equals-whole-array
! covers: IANY-dim-section-wise-reduction
! covers: IANY-dim-mask-section-wise-reduction
program i169m_iany_dim
  implicit none
  integer :: vec(3), grid(2,2), r1, rdim1(2), rdim2(2), rmask(2), checks
  logical :: m2(2,2)
  checks = 0
  vec = [3, 1, 4]
  r1 = iany(vec, dim=1)
  call require('IANY rank-one DIM equals whole-array form', r1 == iany(vec) .and. btest(r1, 0), checks)
  grid = reshape([3, 1, 6, 3], [2, 2])
  rdim1 = iany(grid, dim=1)
  rdim2 = iany(grid, dim=2)
  call require('IANY DIM reduces each selected section', &
       all(rdim1 == [3, 7]) .and. all(rdim2 == [7, 3]), checks)
  m2 = reshape([.true., .true., .true., .false.], [2, 2])
  rmask = iany(grid, dim=1, mask=m2)
  call require('IANY DIM with MASK reduces corresponding sections', &
       all(rmask == [3, 6]) .and. iany(pack(grid(:,2), m2(:,2))) == 6, checks)
  if (checks /= 3) error stop
  write(*,'(a)') 'INTRINSICS 16.9 M IANY DIM OK'
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
end program i169m_iany_dim
