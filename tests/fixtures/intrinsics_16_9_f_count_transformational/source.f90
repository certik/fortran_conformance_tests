program i169f_count_transformational
  implicit none
  logical :: mask2(2,3)
  mask2 = reshape([.true., .false., .true., .true., .false., .false.], [2,3])
  call require_true('count transformational dim rank reduction', &
       size(shape(count(mask2, dim=1))) == 1 .and. size(shape(count(mask2))) == 0)
  write(*,'(a)') 'INTRINSICS 16.9.F COUNT TRANSFORMATIONAL OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169f_count_transformational
