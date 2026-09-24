program i169g_cshift_integer_character_arrays
  implicit none
  integer :: iv(4)
  character(len=3) :: words(4), shifted(4)
  iv = [10, 20, 30, 40]
  words = [character(len=3) :: 'aa1', 'bb2', 'cc3', 'dd4']
  shifted = cshift(words, 1)
  call require_true('integer array shifted', all(cshift(iv, -1) == [40, 10, 20, 30]))
  call require_true('character array shifted', &
       len(cshift(words, 1)) == 3 .and. &
       all(shifted == [character(len=3) :: 'bb2', 'cc3', 'dd4', 'aa1']))
  write(*,'(a)') 'INTRINSICS 16.9.G CSHIFT INTEGER CHARACTER ARRAYS OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169g_cshift_integer_character_arrays
