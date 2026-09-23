program data_statement_s004_runtime_effects
  implicit none
  integer :: repeated(5), boz_value
  character(len=0) :: empty
  character(len=1) :: tail
  character(len=4) :: padded
  character(len=2) :: cut
  data repeated /2*11, 22, 2*33/
  data empty, tail /'discarded', 'Q'/
  data padded, cut /'AB', 'WXYZ'/
  data boz_value /b'110101'/
  if (repeated(1) /= 11) error stop 1
  if (repeated(2) /= 11) error stop 2
  if (repeated(3) /= 22) error stop 3
  if (repeated(4) /= 33) error stop 4
  if (repeated(5) /= 33) error stop 5
  if (len(empty) /= 0) error stop 6
  if (len(tail) /= 1) error stop 7
  if (tail /= 'Q') error stop 8
  if (len(padded) /= 4) error stop 9
  if (padded /= 'AB  ') error stop 10
  if (len(cut) /= 2) error stop 11
  if (cut /= 'WX') error stop 12
  if (radix(boz_value) /= 2) error stop 13
  if (bit_size(boz_value) < 6) error stop 14
  if (boz_value /= 53) error stop 15
  write(*,'(a)') 'DATA STATEMENT S004 RUNTIME EFFECTS OK'
end program data_statement_s004_runtime_effects
