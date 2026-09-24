program i169g_cshift_transformational_rank
  implicit none
  integer :: rect(2,3)
  rect(1,:) = [1, 2, 3]
  rect(2,:) = [4, 5, 6]
  call require_true('rank two result preserved', size(shape(cshift(rect, 1, dim=1))) == 2)
  call require_true('whole array transformed shape', all(shape(cshift(rect, 1, dim=1)) == [2, 3]))
  write(*,'(a)') 'INTRINSICS 16.9.G CSHIFT TRANSFORMATIONAL RANK OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169g_cshift_transformational_rank
