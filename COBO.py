import subprocess
import sys
import scipy
import scipy.optimize
import argparse

parser = argparse.ArgumentParser(prog='COBO', description='Launch correlation based optimizer.')
parser.add_argument('engine' , type = str)
parser.add_argument('depth', type = int)
parser.add_argument('--popsize', type = int)

args = parser.parse_args()

engine = args.engine
depth =  args.depth
popsize = args.popsize

if popsize == None:
  popsize = 15

correlation = 0

multipv = 1
verbose = False

def getPars():
  sf = subprocess.Popen('./' + engine,  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
  sf.stdin.write('isready' + '\n')
  pars = []
  while True:
    outline = sf.stdout.readline().rstrip()
    print outline
    if outline == 'readyok':
      break
    if not outline.startswith('Stockfish'):
      pars.append(outline.split(','))
    
  return pars

Pars = getPars()

def launchSf(locpars):
  if verbose:
    for p in locpars:
      print p[0],p[1]
  sf =subprocess.Popen('./' + engine, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
  sf.stdin.write('setoption name multipv value ' + str(multipv)  + '\n')
  sf.stdin.write('setoption name Hash value 2048' + '\n')

  for par in locpars:
    cmd = 'setoption name ' + par[0] + ' value ' + str(par[1]) + '\n'
    sf.stdin.write(cmd)

  sf.stdin.write('go depth '   + str(depth) + '\n')
  sf.stdin.write('bench 16 1 ' + str(depth-10) + ' balancedMiddlegames.epd\n')
  sf.stdin.write('bench 16 1 ' + str(depth-13) + ' balancedEndgames.epd\n')
  howManyBenches = 0

  while True:
    if howManyBenches == 2:
      break
    outline = sf.stdout.readline().rstrip()
    if outline.startswith('Search/eval correlation'):
      correlationLine = outline
      print '\r' + outline + ' ',
    if outline.startswith('info depth') and verbose:
      print '\n'+outline + ' ',

    if outline.startswith('Total time'):
      howManyBenches += 1

  res = float(correlationLine.split()[2])
  if verbose:
    print '\n' + str(res)

  sf.terminate()
  sf.wait()
  return res


def Array2Pars(parsArray):
  locpars = Pars[:]
  for n, par in enumerate(locpars):
    locpars[n][1] = int(round(float(parsArray[n])))
  return locpars

def Pars2Array(pars):
  parsArray = [par[1] for par in pars]  
  return parsArray


def fitness(parsArray):
  locpars = Array2Pars(parsArray)
  return -launchSf(locpars)
  
def getBounds():
  return [(p[2], p[3]) for p in Pars]

def statusMsg(xk, convergence = 0):
  newPars = Array2Pars(xk)
  print
  for p in newPars:
    print p[0],p[1]
  print
  return False


if __name__ == '__main__':
  f = fitness(Pars2Array(Pars))
  print '\n' +  'Reference correlation: ' + str(-f)
  res = scipy.optimize.differential_evolution(fitness, getBounds(), disp=True, callback = statusMsg, popsize = popsize)
  statusMsg(res.x)
  print 'Search/eval correlation: ', -res.fun
