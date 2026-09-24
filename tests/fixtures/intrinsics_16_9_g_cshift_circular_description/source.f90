program i169g_cshift_circular_description
  implicit none
  integer :: v(6), left(6), right(6)
  v = [1, 2, 3, 4, 5, 6]
  left = cshift(v, 2)
  right = cshift(v, -2)
  call require_true('left circular shift', all(left == [3, 4, 5, 6, 1, 2]))
  call require_true('right circular shift', all(right == [5, 6, 1, 2, 3, 4]))
  write(*,'(a)') 'INTRINSICS 16.9.G CSHIFT CIRCULAR DESCRIPTION OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169g_cshift_circular_description
