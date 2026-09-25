program i169p_len_values
  implicit none
  character(len=5) :: padded = 'AB'
  character(len=3) :: words(2) = [character(len=3) :: 'abc', 'xy']
  character(len=0) :: empty = ''
  character(len=:), allocatable :: allocated_s
  character(len=7), target :: target_s = 'ABCDEFG'
  character(len=:), pointer :: pointer_s
  allocate(character(len=7) :: allocated_s)
  pointer_s => target_s
  call require_true('len scalar character length', len(padded) == 5)
  call require_true('len array element character length', len(words) == 3)
  call require_true('len zero length character', len(empty) == 0)
  call require_true('len allocated deferred length character', len(allocated_s) == 7)
  call require_true('len associated deferred pointer length', len(pointer_s) == 7)
  write(*,'(a)') 'INTRINSICS 16.9.P LEN VALUES OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
  subroutine require_false(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_false
end program i169p_len_values
