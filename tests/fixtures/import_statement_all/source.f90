program import_statement_all_effect
  implicit none
  integer :: hx, hz, observed
  hx = 5
  hz = 100
  observed = -77
  call inner(observed)
  if (observed /= 12) error stop 1
  if (hz /= 7) error stop 2
  write(*,'(a)') 'IMPORT STATEMENT ALL OK'
contains
  subroutine inner(out)
    import, all
    integer, intent(out) :: out
    hz = 7
    out = hx + hz
  end subroutine
end program import_statement_all_effect
