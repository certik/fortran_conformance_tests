program i169e_bge
  implicit none
  logical :: observed
  observed = bge(not(0), 1)
  call require_true('bge true bit-sequence comparison', observed)
  observed = bge(1, not(0))
  call require_false('bge false bit-sequence comparison', observed)
  call require_true('bge result default logical', kind(bge(1, 1)) == kind(.false.))
  write(*,'(a)') 'INTRINSICS 16.9.E BGE ARGUMENTS OK'
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
end program i169e_bge
