program i169g_cshift_argument_controls
  implicit none
  integer :: v(6), m(3,3), r(3,3), expected(3,3)
  v = [1, 2, 3, 4, 5, 6]
  m(1,:) = [1, 2, 3]
  m(2,:) = [4, 5, 6]
  m(3,:) = [7, 8, 9]
  call require_true('rank one scalar integer shift', all(cshift(v, 2) == [3, 4, 5, 6, 1, 2]))
  r = cshift(m, shift=[-1, 1, 0], dim=2)
  expected(1,:) = [3, 1, 2]
  expected(2,:) = [5, 6, 4]
  expected(3,:) = [7, 8, 9]
  call require_true('rank two vector shift shape', all(r == expected))
  r = cshift(m, shift=1, dim=1)
  expected(1,:) = [4, 5, 6]
  expected(2,:) = [7, 8, 9]
  expected(3,:) = [1, 2, 3]
  call require_true('dim one in range selected', all(r == expected))
  write(*,'(a)') 'INTRINSICS 16.9.G CSHIFT ARGUMENT CONTROLS OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169g_cshift_argument_controls
