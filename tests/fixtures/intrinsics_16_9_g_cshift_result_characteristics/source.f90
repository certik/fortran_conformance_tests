program i169g_cshift_result_characteristics
  implicit none
  character(len=3) :: words(4)
  integer :: rect(2,3)
  words = [character(len=3) :: 'aa1', 'bb2', 'cc3', 'dd4']
  rect(1,:) = [1, 2, 3]
  rect(2,:) = [4, 5, 6]
  call require_true('character length parameter preserved', len(cshift(words, 1)) == 3)
  call require_true('rank two shape preserved', all(shape(cshift(rect, 1, dim=2)) == [2, 3]))
  write(*,'(a)') 'INTRINSICS 16.9.G CSHIFT RESULT CHARACTERISTICS OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169g_cshift_result_characteristics
