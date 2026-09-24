program i169g_cshift_rank_two_sections
  implicit none
  integer :: m(3,3), r(3,3), expected(3,3)
  m(1,:) = [1, 2, 3]
  m(2,:) = [4, 5, 6]
  m(3,:) = [7, 8, 9]
  r = cshift(m, shift=-1, dim=2)
  expected(1,:) = [3, 1, 2]
  expected(2,:) = [6, 4, 5]
  expected(3,:) = [9, 7, 8]
  call require_true('rank two scalar shift along dim two', all(r == expected))
  r = cshift(m, shift=[-1, 1, 0], dim=2)
  expected(1,:) = [3, 1, 2]
  expected(2,:) = [5, 6, 4]
  expected(3,:) = [7, 8, 9]
  call require_true('rank two vector shifts by section', all(r == expected))
  write(*,'(a)') 'INTRINSICS 16.9.G CSHIFT RANK TWO SECTIONS OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169g_cshift_rank_two_sections
